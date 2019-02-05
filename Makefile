PYTHON			?= python
CLIPS_VERSION		?= 6.40
CLIPS_SOURCE_URL	?= "https://sourceforge.net/projects/clipsrules/files/CLIPS/6.40_Beta_3/clips_core_source_640.zip "
CLIPS_SOURCE_DIR	?= clips_source
MAKEFILE_NAME		?= makefile
SHARED_LIBRARY_DIR	?= /usr/lib

.PHONY: donwload clips clipspy test install clean

all: download clips clipspy

download:
	wget -O clips.zip $(CLIPS_SOURCE_URL)
	unzip -jo clips.zip -d $(CLIPS_SOURCE_DIR)

clips: download
	$(MAKE) -C $(CLIPS_SOURCE_DIR) -f $(MAKEFILE_NAME)  			\
		CFLAGS='-std=c99 -O3 -fno-strict-aliasing -fPIC'
	ld -G $(CLIPS_SOURCE_DIR)/*.o -o $(CLIPS_SOURCE_DIR)/libclips.so

clipspy: clips
	$(PYTHON) setup.py build_ext --include-dirs $(CLIPS_SOURCE_DIR)       	\
		--library-dirs $(CLIPS_SOURCE_DIR)

test: clipspy
	cp build/lib.*/clips/_clips*.so clips
	LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(CLIPS_SOURCE_DIR)			\
		$(PYTHON) -m pytest -v

install: clipspy
	cp $(CLIPS_SOURCE_DIR)/libclips.so		 			\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)
	ln -s $(SHARED_LIBRARY_DIR)/libclips.so.$(CLIPS_VERSION)		\
	 	$(SHARED_LIBRARY_DIR)/libclips.so.6
	ldconfig -n -v $(SHARED_LIBRARY_DIR)
	$(PYTHON) setup.py install

clean:
	-rm clips.zip
	-rm -fr clips_source build dist clipspy.egg-info
