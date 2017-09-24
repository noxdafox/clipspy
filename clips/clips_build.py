from cffi import FFI

ffibuilder = FFI()

with open("lib/clips.c") as source_file:
    CLIPS_SOURCE = source_file.read()

with open("lib/clips.cdef") as cdef_file:
    CLIPS_CDEF = cdef_file.read()

ffibuilder.set_source("_clips",
                      CLIPS_SOURCE,
                      libraries=["clips"])

ffibuilder.cdef(CLIPS_CDEF)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
