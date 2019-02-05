PYTHON			?= python
CLIPS_VERSION		?= 6.30
CLIPS_SOURCE_URL	?= "https://downloads.sourceforge.net/project/clipsrules/CLIPS/6.30/clips_core_source_630.zip"
CLIPS_SOURCE_DIR	?= clips_source
MAKEFILE_NAME		?= makefile.lib
SHARED_LIBRARY_DIR	?= /usr/lib

.PHONY: donwload clips clipspy test install clean

all: download clips clipspy

download:
	wget -O clips.zip $(CLIPS_SOURCE_URL)
	unzip -jo clips.zip -d $(CLIPS_SOURCE_DIR)

clips: download
	cp $(CLIPS_SOURCE_DIR)/$(MAKEFILE_NAME) $(CLIPS_SOURCE_DIR)/Makefile
	sed -i 's/gcc -c/gcc -fPIC -c/g' $(CLIPS_SOURCE_DIR)/Makefile
	$(MAKE) -C $(CLIPS_SOURCE_DIR)
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
