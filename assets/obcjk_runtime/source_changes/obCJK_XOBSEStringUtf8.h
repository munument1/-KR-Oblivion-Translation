#pragma once
// Experimental, opt-in compatibility for the locally verified xOBSE 22.13 build.
// Only listed StringVar/string-operation calls using CP_ACP are redirected.
// No process-wide API hooks, executable patches, or on-disk xOBSE changes.
#include <windows.h>
#include <intrin.h>
#include <cstring>

static ULONG_PTR g_svModuleBase = 0;
static bool g_svUtf8Enabled = false;
static LONG g_svMbHits = 0, g_svWideHits = 0;
typedef int (WINAPI* ObCJKMbFn)(UINT,DWORD,LPCCH,int,LPWSTR,int);
typedef int (WINAPI* ObCJKWideFn)(UINT,DWORD,LPCWCH,int,LPSTR,int,LPCCH,LPBOOL);
static ObCJKMbFn g_svOriginalMb = nullptr;
static ObCJKWideFn g_svOriginalWide = nullptr;

static bool ObCJKSVCallerAllowed(ULONG_PTR caller, bool wide) {
    if (!g_svModuleBase || caller < g_svModuleBase) return false;
    const ULONG_PTR rva = caller - g_svModuleBase;
    static const DWORD mbCalls[] = {
        0x5AA37,0x5AA68,0x5AFDE,0x5B00D,0x9AFAE,0x9AFD9,
        0x9B249,0x9B274,0x9B340,0x9B368,0x9B45C,0x9B485,
        0x9B5DC,0x9B605,0x9B615,0x9B63E
    };
    static const DWORD wideCalls[] = {0x9B0CD,0x9B0EA,0x9B193,0x9B1B9,0x9B9BE,0x9B9DB};
    const DWORD* calls = wide ? wideCalls : mbCalls;
    const size_t count = wide ? sizeof(wideCalls)/sizeof(DWORD) : sizeof(mbCalls)/sizeof(DWORD);
    for (size_t i=0;i<count;++i) if (rva == calls[i]) return true;
    return false;
}
static UINT ObCJKSVCodePage(UINT cp, ULONG_PTR caller, bool wide) {
    return g_svUtf8Enabled && cp == CP_ACP && ObCJKSVCallerAllowed(caller,wide) ? CP_UTF8 : cp;
}
static int WINAPI ObCJKSV_Mb(UINT cp,DWORD flags,LPCCH src,int n,LPWSTR dst,int cap) {
    const UINT selected = ObCJKSVCodePage(cp,(ULONG_PTR)_ReturnAddress(),false);
    if (selected != cp && InterlockedIncrement(&g_svMbHits)<=8)
        _MESSAGE("obCJK:XOBSEStringUtf8: mb CP_ACP->UTF8 hit=%ld",g_svMbHits);
    return g_svOriginalMb(selected,flags,src,n,dst,cap);
}
static int WINAPI ObCJKSV_Wide(UINT cp,DWORD flags,LPCWCH src,int n,LPSTR dst,int cap,LPCCH def,LPBOOL used) {
    // UTF-8 rejects non-null default-character arguments. Preserve foreign calls.
    const UINT selected = (!def && !used) ? ObCJKSVCodePage(cp,(ULONG_PTR)_ReturnAddress(),true) : cp;
    if (selected != cp && InterlockedIncrement(&g_svWideHits)<=8)
        _MESSAGE("obCJK:XOBSEStringUtf8: wide CP_ACP->UTF8 hit=%ld",g_svWideHits);
    return g_svOriginalWide(selected,flags,src,n,dst,cap,def,used);
}
typedef unsigned char* (__cdecl* ObCJKTokenFn)(unsigned char*,const unsigned char*,unsigned char**);
static ObCJKTokenFn g_svOriginalToken = nullptr;
static LONG g_svTokenHits=0;
static unsigned char* __cdecl ObCJKSV_Token(unsigned char* text,const unsigned char* delimiters,unsigned char** context) {
    ULONG_PTR caller=(ULONG_PTR)_ReturnAddress();
    ULONG_PTR rva=caller-g_svModuleBase;
    bool ascii=delimiters!=nullptr;
    if (ascii) for (const unsigned char* p=delimiters;*p;++p) if (*p>=0x80) { ascii=false;break; }
    if (!g_svUtf8Enabled || !ascii || !context || (rva!=0x499DE && rva!=0x499EC))
        return g_svOriginalToken(text,delimiters,context);
    // UTF-8 continuation bytes cannot equal an ASCII delimiter. Byte scanning
    // preserves every UTF-8 byte, unlike CP949-aware _mbstok_s on an orphan lead.
    unsigned char* p=text ? text : *context;
    if (!p) return nullptr;
    while (*p && strchr((const char*)delimiters,*p)) ++p;
    if (!*p) { *context=p;return nullptr; }
    unsigned char* token=p;
    while (*p && !strchr((const char*)delimiters,*p)) ++p;
    if (*p) *p++=0;
    *context=p;
    if (InterlockedIncrement(&g_svTokenHits)<=8)
        _MESSAGE("obCJK:XOBSEStringUtf8: UI tokenizer UTF8-safe hit=%ld",g_svTokenHits);
    return token;
}
static ULONG_PTR* ObCJKSVImportSlot(HMODULE module,const char* name) {
    BYTE* b=(BYTE*)module;
    IMAGE_DOS_HEADER* dos=(IMAGE_DOS_HEADER*)b;
    IMAGE_NT_HEADERS32* nt=(IMAGE_NT_HEADERS32*)(b+dos->e_lfanew);
    DWORD rva=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (!rva) return nullptr;
    for (IMAGE_IMPORT_DESCRIPTOR* d=(IMAGE_IMPORT_DESCRIPTOR*)(b+rva);d->Name;++d) {
        if (!d->OriginalFirstThunk) continue;
        IMAGE_THUNK_DATA32* names=(IMAGE_THUNK_DATA32*)(b+d->OriginalFirstThunk);
        IMAGE_THUNK_DATA32* slots=(IMAGE_THUNK_DATA32*)(b+d->FirstThunk);
        for (;names->u1.AddressOfData;++names,++slots) {
            if (IMAGE_SNAP_BY_ORDINAL32(names->u1.Ordinal)) continue;
            IMAGE_IMPORT_BY_NAME* entry=(IMAGE_IMPORT_BY_NAME*)(b+names->u1.AddressOfData);
            if (!strcmp((const char*)entry->Name,name)) return (ULONG_PTR*)&slots->u1.Function;
        }
    }
    return nullptr;
}
static bool ObCJKSVWriteSlot(ULONG_PTR* slot,ULONG_PTR value) {
    DWORD old=0,ignored=0;
    if (!VirtualProtect(slot,sizeof(*slot),PAGE_READWRITE,&old)) return false;
    InterlockedExchange((volatile LONG*)slot,(LONG)value);
    VirtualProtect(slot,sizeof(*slot),old,&ignored);
    return true;
}
static void ObCJKInstallXOBSEStringUtf8() {
    if (g_activeCodePage != kCP_UTF8 || !GetPrivateProfileIntA("obCJK","XOBSEStringUtf8Enable",0,k_iniMain)) {
        _MESSAGE("obCJK:XOBSEStringUtf8: disabled (opt-in, UTF8 only)"); return;
    }
    HMODULE module=GetModuleHandleA("obse_1_2_416.dll");
    if (!module) { _WARNING("obCJK:XOBSEStringUtf8: xOBSE module absent, skipped"); return; }
    BYTE* b=(BYTE*)module;
    IMAGE_DOS_HEADER* dos=(IMAGE_DOS_HEADER*)b;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;
    IMAGE_NT_HEADERS32* nt=(IMAGE_NT_HEADERS32*)(b+dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->FileHeader.Machine != IMAGE_FILE_MACHINE_I386 ||
        nt->FileHeader.TimeDateStamp != 0x684B4FE5 || nt->OptionalHeader.SizeOfImage != 0x125000) {
        _WARNING("obCJK:XOBSEStringUtf8: unsupported xOBSE binary, skipped"); return;
    }
    ULONG_PTR* mb=ObCJKSVImportSlot(module,"MultiByteToWideChar");
    ULONG_PTR* wide=ObCJKSVImportSlot(module,"WideCharToMultiByte");
    ULONG_PTR* token=ObCJKSVImportSlot(module,"_mbstok_s");
    if (!token || (BYTE*)token-b != 0xAA240 || !mb || !wide || (BYTE*)mb-b != 0xAA034 || (BYTE*)wide-b != 0xAA038 ||
        *mb != (ULONG_PTR)&MultiByteToWideChar || *wide != (ULONG_PTR)&WideCharToMultiByte) {
        _WARNING("obCJK:XOBSEStringUtf8: import mismatch or existing hook, skipped"); return;
    }
    g_svModuleBase=(ULONG_PTR)b;
    const DWORD mbReturns[] = {0x5AA37,0x5AA68,0x5AFDE,0x5B00D,0x9AFAE,0x9AFD9,0x9B249,0x9B274,0x9B340,0x9B368,0x9B45C,0x9B485,0x9B5DC,0x9B605,0x9B615,0x9B63E};
    const DWORD wideReturns[] = {0x9B0CD,0x9B0EA,0x9B193,0x9B1B9,0x9B9BE,0x9B9DB};
    for (DWORD r : mbReturns) {
        if (b[r-2]!=0xFF || (b[r-1]!=0xD7 && b[r-1]!=0xD3)) {
            _WARNING("obCJK:XOBSEStringUtf8: mb call-site mismatch, skipped"); return;
        }
    }
    for (DWORD r : wideReturns) {
        bool indirect=b[r-2]==0xFF && b[r-1]==0xD7;
        bool iat=b[r-6]==0xFF && b[r-5]==0x15 && *(ULONG_PTR*)(b+r-4)==(ULONG_PTR)wide;
        if (!indirect && !iat) { _WARNING("obCJK:XOBSEStringUtf8: wide call-site mismatch, skipped"); return; }
    }
    if (b[0x499DC]!=0xFF || b[0x499DD]!=0xD6 || b[0x499EA]!=0xFF || b[0x499EB]!=0xD6) {
        _WARNING("obCJK:XOBSEStringUtf8: tokenizer call-site mismatch, skipped");return;
    }
    g_svOriginalToken=(ObCJKTokenFn)*token;
    g_svOriginalMb=(ObCJKMbFn)*mb; g_svOriginalWide=(ObCJKWideFn)*wide;
    if (!ObCJKSVWriteSlot(mb,(ULONG_PTR)&ObCJKSV_Mb)) return;
    if (!ObCJKSVWriteSlot(wide,(ULONG_PTR)&ObCJKSV_Wide)) {
        ObCJKSVWriteSlot(mb,(ULONG_PTR)g_svOriginalMb); return;
    }
    if (!ObCJKSVWriteSlot(token,(ULONG_PTR)&ObCJKSV_Token)) {
        ObCJKSVWriteSlot(mb,(ULONG_PTR)g_svOriginalMb);
        ObCJKSVWriteSlot(wide,(ULONG_PTR)g_svOriginalWide); return;
    }
    g_svUtf8Enabled=true;
    _MESSAGE("obCJK:XOBSEStringUtf8: installed test2; xOBSE22.13, 16 mb / 6 wide + 2 UI tokenizer call sites, CP_ACP->UTF8");
}
