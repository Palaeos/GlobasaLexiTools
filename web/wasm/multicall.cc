// Dispatcher for the multicall Apertium binary: callMain([tool, args...]).
// The JS runner writes the stream to /io/in and reads /io/out afterwards; both
// are put on fds 0/1 here so every tool (stdio, InputFile, ICU u_finit) sees
// ordinary stdin/stdout. One fresh module instance per call (EXIT_RUNTIME=1),
// so getopt and static state never leak from one step into the next.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

int lt_proc_main(int, char**);
int cg_proc_main(int, char**);
int apertium_tagger_main(int, char**);
int apertium_pretransfer_main(int, char**);
int lrx_proc_main(int, char**);
int lsx_proc_main(int, char**);
int apertium_anaphora_main(int, char**);
int rtx_proc_main(int, char**);
int apertium_destxt_main(int, char**);
int apertium_retxt_main(int, char**);
int apertium_normalize_main(int, char**);
int apertium_wblank_attach_main(int, char**);
int apertium_wblank_detach_main(int, char**);

struct Tool { const char* name; int (*fn)(int, char**); };
static const Tool TOOLS[] = {
  {"lt-proc", lt_proc_main}, {"cg-proc", cg_proc_main},
  {"apertium-tagger", apertium_tagger_main}, {"apertium-pretransfer", apertium_pretransfer_main},
  {"lrx-proc", lrx_proc_main}, {"lsx-proc", lsx_proc_main},
  {"apertium-anaphora", apertium_anaphora_main}, {"rtx-proc", rtx_proc_main},
  {"apertium-destxt", apertium_destxt_main}, {"apertium-retxt", apertium_retxt_main},
  {"apertium-normalize", apertium_normalize_main},
  {"apertium-wblank-attach", apertium_wblank_attach_main},
  {"apertium-wblank-detach", apertium_wblank_detach_main},
};

int main(int argc, char** argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: <tool> [args...]\n");
    return 2;
  }
  int in = open("/io/in", O_RDONLY);
  if (in >= 0) { dup2(in, 0); close(in); }
  int out = open("/io/out", O_WRONLY | O_CREAT | O_TRUNC, 0644);
  if (out >= 0) { dup2(out, 1); close(out); }
  for (const Tool& t : TOOLS) {
    if (strcmp(argv[1], t.name) == 0) {
      return t.fn(argc - 1, argv + 1);
    }
  }
  fprintf(stderr, "unknown tool: %s\n", argv[1]);
  return 2;
}
