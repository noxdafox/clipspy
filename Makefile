PYTHON			?= python
CLIPS_VERSION		?= 6.40
CLIPS_SOURCE_URL	?= "https://sourceforge.net/projects/clipsrules/files/CLIPS/6.40_Beta_3/clips_core_source_640.zip "
MAKEFILE_NAME		?= makefile
SHARED_LIBRARY_DIR	?= /usr/lib

.PHONY: clips clipspy test install clean

all: clips_source clips clipspy

clips_source:
	wget -O clips.zip $(CLIPS_SOURCE_URL)
	unzip -jo clips.zip -d clips_source

clips: clips_source
	$(MAKE) -C clips_source -f $(MAKEFILE_NAME)  			\
		CFLAGS='-std=c99 -O3 -fno-strict-aliasing -fPIC'
	ld -G clips_source/*.o -o clips_source/libclips.so

clipspy: clips
	$(PYTHON) setup.py build_ext --include-dirs clips_source       	\
		--library-dirs clips_source

test: clipspy
	cp build/lib.*/clips/_clips*.so clips
	LD_LIBRARY_PATH=$LD_LIBRARY_PATH:clips_source			\
		$(PYTHON) -m pytest -v

install: clipspy
	cp clips_source/libclips.so		 			\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)
	ln -s $(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)	\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.6
	ln -s $(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)	       \
	 	$(SHARED_LIBRARY_DIR)/libclips.so
	-ldconfig -n -v $(SHARED_LIBRARY_DIR)

install: clipspy install-clips
	$(PYTHON) setup.py install

clean:
	-rm clips.zip
	-rm -fr clips_source build dist clipspy.egg-info
