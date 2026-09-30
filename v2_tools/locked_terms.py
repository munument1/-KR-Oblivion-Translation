from __future__ import annotations
import csv,re,collections
from pathlib import Path

ROLE_MARKERS=("OBJ","SUBJ","TOPIC","WITH","DIR","VOC","GEN","FROM")
PAIRED_PARTICLES=("으로","을","를","이","가","은","는","과","와","로","아","야")

def load_lock_rules(path: Path):
    exact={}
    phrases=[]
    with path.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            en=(row.get("source_english") or "").strip()
            ko=(row.get("korean") or "").strip()
            app=(row.get("application") or "").strip()
            if not en or not ko:
                continue
            if app=="PHRASE_CONTEXT":
                tail=r"(?:'s|s)?" if not en.casefold().endswith("s") else ""
                pat=re.compile(r"(?<![A-Za-z0-9])"+re.escape(en)+tail+r"(?![A-Za-z0-9])")
                phrases.append((en,ko,pat))
            else:
                exact[en.casefold()]=(en,ko)
    phrases.sort(key=lambda x:len(x[0]),reverse=True)
    return exact,phrases
def collect_hits(source, item_hits, exact, phrases):
    pair=exact.get(source.strip().casefold())
    if pair:
        return [{"source":pair[0],"target":pair[1],"basis":"RUNTIME_EXACT"}]
    merged={}
    for en,ko,pat in phrases:
        if pat.search(source):
            merged[en]={"source":en,"target":ko,"basis":"RUNTIME_LOCKED"}
    for h in item_hits or []:
        en=(h.get("source") or "").strip()
        ko=(h.get("target") or "").strip()
        if en and ko and en not in merged:
            merged[en]={"source":en,"target":ko,"basis":h.get("basis","BATCH_GLOSSARY")}
    return sorted(merged.values(),key=lambda x:len(x["source"]),reverse=True)

def protect_source(source, item_hits, exact, phrases):
    hits=collect_hits(source,item_hits,exact,phrases)
    matches=[]
    for h in hits:
        en=h["source"]
        tail=r"(?:'s|s)?" if not en.casefold().endswith("s") else ""
        pat=re.compile(r"(?<![A-Za-z0-9])"+re.escape(en)+tail+r"(?![A-Za-z0-9])")
        for m in pat.finditer(source):
            matches.append((m.start(),m.end(),h))
    matches.sort(key=lambda x:(x[0],-(x[1]-x[0])))
    selected=[]; end=-1
    for m in matches:
        if m[0]>=end:
            selected.append(m); end=m[1]
    if not selected:
        return source,[],hits
    out=[]; mapping=[]; pos=0
    for idx,(start,stop,h) in enumerate(selected,1):
        token=f"__PN{idx:03d}__"
        out.append(source[pos:start]); out.append(token)
        mapping.append({"token":token,"english":source[start:stop],"rule_source":h["source"],"target":h["target"]})
        pos=stop
    out.append(source[pos:])
    return "".join(out),mapping,hits
def _last_hangul(text):
    for ch in reversed(text):
        o=ord(ch)
        if 0xAC00<=o<=0xD7A3:
            return ch
    return None

def choose_josa(target, role):
    ch=_last_hangul(target)
    if ch is None:
        # Fallback for rare non-Hangul targets: prefer vowel-side forms.
        return {"OBJ":"를","SUBJ":"가","TOPIC":"는","WITH":"와","DIR":"로","VOC":"야"}[role]
    jong=(ord(ch)-0xAC00)%28
    has=jong!=0
    rieul=jong==8
    if role=="OBJ": return "을" if has else "를"
    if role=="SUBJ": return "이" if has else "가"
    if role=="TOPIC": return "은" if has else "는"
    if role=="WITH": return "과" if has else "와"
    if role=="DIR": return "로" if (not has or rieul) else "으로"
    if role=="VOC": return "아" if has else "야"
    if role=="GEN": return "의"
    if role=="FROM": return ("로" if (not has or rieul) else "으로")+"부터"
    raise ValueError(role)

PLAIN_TO_ROLE={"을":"OBJ","를":"OBJ","이":"SUBJ","가":"SUBJ",
               "은":"TOPIC","는":"TOPIC","과":"WITH","와":"WITH",
               "으로":"DIR","로":"DIR","아":"VOC","야":"VOC"}
SLASH_ROLE_PATTERNS=[
    ("DIR",r"(?:으로|로)/(?:으로|로)"),
    ("OBJ",r"(?:을|를)/(?:을|를)"),
    ("SUBJ",r"(?:이|가)/(?:이|가)"),
    ("TOPIC",r"(?:은|는)/(?:은|는)"),
    ("WITH",r"(?:과|와)/(?:과|와)"),
    ("VOC",r"(?:아|야)/(?:아|야)"),
]
PAREN_ROLE_PATTERNS=[
    ("DIR",r"(?:\(으\)로|으\(로\)|로\(으\)|으로\(로\)|로\(으로\))"),
    ("OBJ",r"(?:을\(를\)|를\(을\)|\(을\)를|\(를\)을)"),
    ("SUBJ",r"(?:이\(가\)|가\(이\)|\(이\)가|\(가\)이)"),
    ("TOPIC",r"(?:은\(는\)|는\(은\)|\(은\)는|\(는\)은)"),
    ("WITH",r"(?:과\(와\)|와\(과\)|\(과\)와|\(와\)과)"),
    ("VOC",r"(?:아\(야\)|야\(아\)|\(아\)야|\(야\)아)"),
    ("GEN",r"(?:의\(의\))"),
    ("FROM",r"(?:\(으\)로부터|으\(로\)부터|으로부터\(로부터\)|로부터\(으로부터\))"),
]
DOUBLE_ROLE_PATTERNS=[
    ("DIR",r"(?:으로|로){2}"),("OBJ",r"(?:을|를){2}"),
    ("SUBJ",r"(?:이|가){2}"),("TOPIC",r"(?:은|는){2}"),
    ("WITH",r"(?:과|와){2}"),("VOC",r"(?:아|야){2}"),
]
FIXED_PARTICLES=("에서","에게","한테","부터","까지","께서","의","에","도","만")
MARKER_TRAIL=r"(?:\s*(?:으로부터|로부터|\([을를이가은는과와아야의]\)|\(으\)로|으\(로\)|로\(으\)|으로\(로\)|로\(으로\)|을\(를\)|를\(을\)|\(을\)를|\(를\)을|이\(가\)|가\(이\)|\(이\)가|\(가\)이|은\(는\)|는\(은\)|\(은\)는|\(는\)은|과\(와\)|와\(과\)|\(과\)와|\(와\)과|아\(야\)|야\(아\)|\(아\)야|\(야\)아|으로/로|로/으로|을/를|를/을|이/가|가/이|은/는|는/은|과/와|와/과|아/야|야/아|으로|로|을|를|이|가|은|는|과|와|아|야|의|에|에서|에게|한테|도|만|부터|까지|께서)(?![가-힣]))?"

def restore_locked(text, mapping):
    out=text
    # Gemini occasionally materializes the supplied final Korean name instead of copying
    # the opaque token. Accept that only when the exact locked target was already present
    # in the model output; otherwise a missing token still fails.
    direct_available=collections.Counter()
    for m in mapping:
        direct_available[m["target"]]=text.count(m["target"])
    direct_used=collections.Counter()
    for m in mapping:
        token=m["token"]; target=m["target"]
        token_count=out.count(token)
        if token_count==0:
            if direct_used[target] < direct_available[target]:
                # Gemini may leak the opaque token's numeric suffix while materializing
                # the Korean target, e.g. __PN001__ -> "쉐오고라스1이".
                tm=re.fullmatch(r"__PN(\d{3})__",token)
                if tm:
                    idx=int(tm.group(1))
                    suffixes=sorted({str(idx),f"{idx:02d}",f"{idx:03d}"},key=len,reverse=True)
                    suffix_alt="|".join(re.escape(x) for x in suffixes)
                    # The numeric suffix is the leaked PN token index itself.
                    # Because it is glued directly to the confirmed Korean target, strip it
                    # regardless of the following character (e.g. "타이버 셉팀1 탈로스2").
                    leak_pat=re.compile(re.escape(target)+r"(?:"+suffix_alt+r")")
                    out=leak_pat.sub(target,out,count=1)
                # Gemini may output the final Korean target directly while still
                # preserving our particle marker, e.g. "비탄{OBJ}".
                direct_marker_pat=re.compile(re.escape(target)+r"\s*\{("+"|".join(ROLE_MARKERS)+r")\}"+MARKER_TRAIL)
                dm=direct_marker_pat.search(out)
                if dm:
                    out=out[:dm.start()]+target+choose_josa(target,dm.group(1))+out[dm.end():]
                else:
                    # Also normalize model-written paired/parenthetical particles
                    # after a directly materialized Korean target.
                    fixed=False
                    for role,particle_pat in PAREN_ROLE_PATTERNS:
                        pp=re.compile(re.escape(target)+r"\s*("+particle_pat+r")")
                        pm=pp.search(out)
                        if pm:
                            out=out[:pm.start()]+target+choose_josa(target,role)+out[pm.end():]
                            fixed=True
                            break
                    if not fixed:
                        for role,particle_pat in SLASH_ROLE_PATTERNS:
                            sp=re.compile(re.escape(target)+r"\s*("+particle_pat+r")")
                            sm=sp.search(out)
                            if sm:
                                out=out[:sm.start()]+target+choose_josa(target,role)+out[sm.end():]
                                fixed=True
                                break
                    if not fixed:
                        plain_direct=re.compile(re.escape(target)+r"\s*(으로|을|를|이|가|은|는|과|와|로|아|야)")
                        pd=plain_direct.search(out)
                        if pd:
                            role=PLAIN_TO_ROLE[pd.group(1)]
                            out=out[:pd.start()]+target+choose_josa(target,role)+out[pd.end():]
                direct_used[target]+=1
                continue
            raise ValueError(f"locked token/target missing {token}")
        if token_count!=1:
            raise ValueError(f"locked token count mismatch {token}: {token_count}")
        marker_pat=re.compile(re.escape(token)+r"\s*\{("+"|".join(ROLE_MARKERS)+r")\}"+MARKER_TRAIL)
        mm=marker_pat.search(out)
        if mm:
            out=out[:mm.start()]+target+choose_josa(target,mm.group(1))+out[mm.end():]
            continue
        paren_done=False
        for role,particle_pat in PAREN_ROLE_PATTERNS:
            pp=re.compile(re.escape(token)+r"\s*("+particle_pat+r")")
            pmk=pp.search(out)
            if pmk:
                out=out[:pmk.start()]+target+choose_josa(target,role)+out[pmk.end():]
                paren_done=True
                break
        if paren_done:
            continue
        slash_done=False
        for role,particle_pat in SLASH_ROLE_PATTERNS:
            sp=re.compile(re.escape(token)+r"\s*("+particle_pat+r")")
            sm=sp.search(out)
            if sm:
                out=out[:sm.start()]+target+choose_josa(target,role)+out[sm.end():]
                slash_done=True
                break
        if slash_done:
            continue
        fixed_alt="|".join(sorted((re.escape(x) for x in FIXED_PARTICLES),key=len,reverse=True))
        fp=re.compile(re.escape(token)+r"\s*("+fixed_alt+r")/\1")
        fm=fp.search(out)
        if fm:
            out=out[:fm.start()]+target+fm.group(1)+out[fm.end():]
            continue
        double_done=False
        for role,particle_pat in DOUBLE_ROLE_PATTERNS:
            dp=re.compile(re.escape(token)+r"\s*("+particle_pat+r")(?=\s|[.,!?;:)\]\"']|$)")
            dm=dp.search(out)
            if dm:
                out=out[:dm.start()]+target+choose_josa(target,role)+out[dm.end():]
                double_done=True
                break
        if double_done:
            continue
        plain_pat=re.compile(re.escape(token)+r"\s*(으로|을|를|이|가|은|는|과|와|로|아|야)")
        pm=plain_pat.search(out)
        if pm:
            role=PLAIN_TO_ROLE[pm.group(1)]
            out=out[:pm.start()]+target+choose_josa(target,role)+out[pm.end():]
            continue
        out=out.replace(token,target,1)
    if re.search(r"__PN\d{3}__",out):
        raise ValueError("unresolved locked token")
    if re.search(r"\{[A-Z_]+\}",out):
        raise ValueError("unresolved or unknown particle marker")
    return out

LOCK_INSTRUCTION=(
    "Locked proper-name tokens such as __PN001__ must be copied exactly once and never translated, "
    "renamed, omitted, duplicated, or reordered. When a locked token needs a Korean paired particle, "
    "write one allowed marker immediately after it: {OBJ}=을/를, {SUBJ}=이/가, {TOPIC}=은/는, "
    "{WITH}=과/와, {DIR}=으로/로, {VOC}=아/야, {GEN}=의, {FROM}=으로부터/로부터. "
    "IMPORTANT: do not choose {GEN} merely because the English uses possessive 's, 'of', or a noun chain. "
    "Use {GEN} only when explicit '의' is genuinely natural and necessary in Korean; otherwise restructure the phrase naturally and omit it. "
    "Do not invent any other brace marker and do not append a second Korean particle after a marker. "
    "The local postprocessor chooses the correct form from the final Korean name. Fixed particles such as "
    "에, 에서, 에게, 도, 만, 부터, 까지는 may be written directly after the token."
)

FORMAT_RE=re.compile(r"(<[^>]+>|\[pagebreak\]|\r\n|\n|\r|%(?:[-+0#]*\d*(?:\.\d+)?[a-zA-Z%]))",re.I)

def protect_format_tokens(text):
    mapping=[]; parts=[]; pos=0
    for i,m in enumerate(FORMAT_RE.finditer(text),1):
        parts.append(text[pos:m.start()])
        token=f"__FMT{i:03d}__"
        parts.append(token)
        mapping.append({"token":token,"raw":m.group(0)})
        pos=m.end()
    parts.append(text[pos:])
    return "".join(parts),mapping

def restore_format_tokens(text,mapping):
    out=text
    for m in mapping:
        token=m["token"]
        if out.count(token)!=1:
            raise ValueError(f"format token count mismatch {token}: {out.count(token)}")
        out=out.replace(token,m["raw"],1)
    if re.search(r"__FMT\d{3}__",out):
        raise ValueError("unresolved format token")
    return out

FORMAT_INSTRUCTION=(
    "Opaque __FMT###__ tokens represent original markup, line breaks, pagebreaks, or printf placeholders. "
    "Copy every __FMT###__ token exactly once, in the same relative position. Never translate, delete, duplicate, or edit them."
)

FIXED_PAREN_PARTICLES=("에서","에게","한테","부터","까지","께서","의","에","도","만")

def normalize_josa_artifacts(text):
    out=text
    # Resolve paired-particle notation after an ordinary Hangul-ending word,
    # even when the word was not glossary-locked.
    all_role_patterns=PAREN_ROLE_PATTERNS+SLASH_ROLE_PATTERNS+DOUBLE_ROLE_PATTERNS
    for role,particle_pat in all_role_patterns:
        pat=re.compile(r"([가-힣]+)\s*("+particle_pat+r")")
        def repl(m,role=role):
            stem=m.group(1)
            return stem+choose_josa(stem,role)
        out=pat.sub(repl,out)
    # Fixed particles do not need phonological selection: 에(에) -> 에, 의(의) -> 의.
    for particle in FIXED_PAREN_PARTICLES:
        out=re.sub(re.escape(particle)+r"\("+re.escape(particle)+r"\)",particle,out)
        out=re.sub(re.escape(particle)+r"/"+re.escape(particle),particle,out)
    return out

UNRESOLVED_JOSA_RE=re.compile(
    r"(?:을|를)/(?:을|를)|(?:이|가)/(?:이|가)|(?:은|는)/(?:은|는)|(?:과|와)/(?:과|와)|"
    r"(?:으로|로)/(?:으로|로)|(?:아|야)/(?:아|야)|"
    r"을\(를\)|를\(을\)|\(을\)를|\(를\)을|"
    r"이\(가\)|가\(이\)|\(이\)가|\(가\)이|"
    r"은\(는\)|는\(은\)|\(은\)는|\(는\)은|"
    r"과\(와\)|와\(과\)|\(과\)와|\(와\)과|"
    r"아\(야\)|야\(아\)|\(아\)야|\(야\)아|"
    r"\(으\)로|으\(로\)|로\(으\)|으로\(로\)|로\(으로\)|"
    r"(?:에서|에게|한테|부터|까지|께서|의|에|도|만)\((?:에서|에게|한테|부터|까지|께서|의|에|도|만)\)"
)
