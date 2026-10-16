#include <windows.h>
#include <cstdio>
#include <vector>
#include <string>
#include <cassert>
#include <mbstring.h>
#include <mbctype.h>
#define _MESSAGE(...) ((void)0)
#define _WARNING(...) ((void)0)
static int g_activeCodePage=65001;
static const int kCP_UTF8=65001;
static const char* k_iniMain="unused.ini";
#include "obse_plugin_example/include/obCJK_XOBSEStringUtf8.h"

static BYTE* MakeCaller(BYTE* base,DWORD returnRva,void* target,int args,bool cdeclTarget=false) {
    BYTE* start=base+returnRva-(args*4+7);
    BYTE* p=start;
    for (int i=0;i<args;++i) { *p++=0xFF;*p++=0x74;*p++=0x24;*p++=(BYTE)(args*4); }
    *p++=0xB8; *(DWORD*)p=(DWORD)target;p+=4;
    *p++=0xFF;*p++=0xD0;
    assert(p==base+returnRva);
    if (cdeclTarget) { *p++=0x83;*p++=0xC4;*p++=(BYTE)(args*4); }
    *p++=0xC2;*p++=(BYTE)(args*4);*p++=0;
    FlushInstructionCache(GetCurrentProcess(),start,p-start);
    return start;
}
static std::string Roundtrip(const char* s,ObCJKMbFn mb,ObCJKWideFn wide) {
    int n=mb(CP_ACP,0,s,-1,nullptr,0);assert(n>0);
    std::vector<wchar_t> w(n);assert(mb(CP_ACP,0,s,-1,w.data(),n)==n);
    int m=wide(CP_ACP,0,w.data(),-1,nullptr,0,nullptr,nullptr);assert(m>0);
    std::vector<char> b(m);assert(wide(CP_ACP,0,w.data(),-1,b.data(),m,nullptr,nullptr)==m);
    return b.data();
}
int main() {
    BYTE* base=(BYTE*)VirtualAlloc(nullptr,0x125000,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);assert(base);
    g_svModuleBase=(ULONG_PTR)base;g_svUtf8Enabled=true;
    g_svOriginalMb=&MultiByteToWideChar;g_svOriginalWide=&WideCharToMultiByte;
    auto mb=(ObCJKMbFn)MakeCaller(base,0x9AFAE,(void*)&ObCJKSV_Mb,6);
    auto wide=(ObCJKWideFn)MakeCaller(base,0x9B0CD,(void*)&ObCJKSV_Wide,8);
    const char* cases[]={"초기화 완료. 사용 UI: Northern UI.","힘","지능","의지력","민첩성","속도","지구력","친화력","행운","ASCII 123 +5%","", "가😀끝"};
    int damaged=0;
    for (const char* s:cases) {
        if (Roundtrip(s,&MultiByteToWideChar,&WideCharToMultiByte)!=s) ++damaged;
        assert(Roundtrip(s,mb,wide)==s);
    }
    assert(g_svMbHits>0 && g_svWideHits>0);
    // Explicit codepages, unrelated callers, and disabled mode remain unchanged.
    assert(ObCJKSVCodePage(949,(ULONG_PTR)base+0x9AFAE,false)==949);
    assert(ObCJKSVCodePage(0,(ULONG_PTR)base+0x1000,false)==0);
    assert(ObCJKSVCodePage(0,(ULONG_PTR)base+0x9AFAE,true)==0);
    _setmbcp(949);
    g_svOriginalToken=&_mbstok_s;
    typedef unsigned char* (WINAPI* TestToken)(unsigned char*,const unsigned char*,unsigned char**);
    auto tokenize=(TestToken)MakeCaller(base,0x499DE,(void*)&ObCJKSV_Token,3,true);
    auto nextToken=tokenize;
    for (const char* label:cases) {
        if (!*label) continue;
        std::string text=std::string("user16|")+label;
        std::vector<unsigned char> buffer(text.begin(),text.end());buffer.push_back(0);
        unsigned char* context=nullptr;
        assert(!strcmp((char*)tokenize(buffer.data(),(const unsigned char*)"|",&context),"user16"));
        assert(!strcmp((char*)nextToken(nullptr,(const unsigned char*)"|",&context),label));
        assert(nextToken(nullptr,(const unsigned char*)"|",&context)==nullptr);
    }
    printf("PASS: 11 CP949-locale UI tokenizer cases preserve every UTF8 byte.\n");
    g_svUtf8Enabled=false;
    assert(ObCJKSVCodePage(0,(ULONG_PTR)base+0x9AFAE,false)==0);
    assert(Roundtrip("힘",mb,wide)==Roundtrip("힘",&MultiByteToWideChar,&WideCharToMultiByte));
    VirtualFree(base,0,MEM_RELEASE);
    printf("PASS: 12 x86 wrapper roundtrips; %d damaged without fix at ACP=%u; caller/encoding/disable guards passed.\n",damaged,GetACP());
}
