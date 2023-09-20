# vim: tabstop=8
PYTHON			?= python
CLIPS_VERSION		?= 6.41
CLIPS_SOURCE_URL	?= "https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.1/clips_core_source_641.zip"
MAKEFILE_NAME		?= makefile
SHARED_INCLUDE_DIR	?= /usr/local/include
SHARED_LIBRARY_DIR	?= /usr/local/lib
TARGET_ARCH		?= $(shell uname -m)
LINUX_LDLIBS		?= -lm -lrt
OSX_LDLIBS		?= -lm -L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib

# platform detection
PLATFORM = $(shell uname -s)

.PHONY: clips clipspy test install clean

all: clips_source clips clipspy

clips_source:
	curl --output clips.zip --location --url $(CLIPS_SOURCE_URL)
	unzip -jo clips.zip -d clips_source

ifeq ($(PLATFORM),Darwin) # macOS
clips: clips_source
	$(MAKE) -f $(MAKEFILE_NAME) -C clips_source				\
		CFLAGS="-std=c99 -O3 -fno-strict-aliasing -fPIC"		\
		LDLIBS="$(OSX_LDLIBS)"
	ld clips_source/*.o -dylib $(OSX_LDLIBS) -arch $(TARGET_ARCH)		\
		-o clips_source/libclips.so
else
clips: clips_source
	$(MAKE) -f $(MAKEFILE_NAME) -C clips_source				\
		CFLAGS="-std=c99 -O3 -fno-strict-aliasing -fPIC"		\
		LDLIBS="$(LINUX_LDLIBS)"
	ld -G clips_source/*.o -o clips_source/libclips.so
endif

clipspy: clips
	$(PYTHON) setup.py build_ext --include-dirs=clips_source/ 		\
		--library-dirs=clips_source/
	$(PYTHON) setup.py sdist bdist_wheel

test: clipspy
	cp build/lib.*/clips/_clips*.so clips
	LD_LIBRARY_PATH=$LD_LIBRARY_PATH:clips_source				\
		$(PYTHON) -m pytest -v

install-clips: clips
	install -d $(SHARED_INCLUDE_DIR)/
	install -m 644 clips_source/clips.h $(SHARED_INCLUDE_DIR)/
	install -d $(SHARED_INCLUDE_DIR)/clips
	install -m 644 clips_source/*.h $(SHARED_INCLUDE_DIR)/clips/
	install -d $(SHARED_LIBRARY_DIR)/
	install -m 644 clips_source/libclips.so					\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)
	ln -sf $(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)		\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.6
	ln -sf $(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)		\
	 	$(SHARED_LIBRARY_DIR)/libclips.so
	-ldconfig -n -v $(SHARED_LIBRARY_DIR)

install: clipspy install-clips
	$(PYTHON) setup.py install

clean:
	-rm clips.zip
	-rm -fr clips_source build dist clipspy.egg-info
