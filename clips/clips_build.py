from cffi import FFI


ffibuilder = FFI()
CLIPS_SOURCE = """
#include <clips.h>

/* Return true if the template is implied. */
bool ImpliedDeftemplate(Deftemplate *template)
{
    return template->implied;
}

/* User Defined Functions support. */
static void python_function(Environment *env, UDFContext *udfc, UDFValue *out);

int DefinePythonFunction(Environment *environment)
{
    return AddUDF(
        environment, "python-function",
        NULL, UNBOUNDED, UNBOUNDED, NULL,
        python_function, "python_function", NULL);
}
"""


with open("lib/clips.cdef") as cdef_file:
    CLIPS_CDEF = cdef_file.read()


ffibuilder.set_source("_clips",
                      CLIPS_SOURCE,
                      libraries=["clips"])


ffibuilder.cdef(CLIPS_CDEF)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
