# vim: tabstop=8
PYTHON			?= python
CLIPS_VERSION		?= 6.42
CLIPS_SOURCE_URL	?= "https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.2/clips_core_source_642.zip"
LIBS_DIR		?= $(PWD)/libs
DIST_DIR		?= $(PWD)/dist
MAKEFILE_NAME		?= makefile
WHEEL_PLATFORM		?= manylinux2014_x86_64
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
	mkdir -p $(LIBS_DIR)
	$(MAKE) -f $(MAKEFILE_NAME) -C clips_source				\
		CFLAGS="-std=c99 -O3 -fno-strict-aliasing -fPIC"		\
		LDLIBS="$(LINUX_LDLIBS)"
	ld -G clips_source/*.o -o $(LIBS_DIR)/libclips.so
endif

build: clips
	mkdir -p $(DIST_DIR)
	$(PYTHON) -m build --sdist --wheel --outdir $(DIST_DIR)

repair: export LD_LIBRARY_PATH := $LD_LIBRARY_PATH:$(LIBS_DIR)
repair: build
	if ! auditwheel show $(DIST_DIR)/*.whl; then				\
		echo "Skipping non-platform wheel $$wheel";			\
	else									\
		auditwheel repair $(DIST_DIR)/*.whl				\
			--plat $(WHEEL_PLATFORM)				\
			--wheel-dir $(DIST_DIR);				\
	fi									\

clipspy: build repair

test: export LD_LIBRARY_PATH := $LD_LIBRARY_PATH:$(LIBS_DIR)
test: clipspy
	cp build/lib.*/clips/_clips*.so clips
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

install: clipspy
	$(PYTHON) setup.py install

clean:
	-rm clips.zip
	-rm -fr clips_source build dist clipspy.egg-info
