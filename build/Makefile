
# ====== JITPCB Environment ====================================================

ifndef JITPCB_SRC_ROOT
JITPCB_SRC_ROOT = ..
endif

ifdef JITPCB_ROOT
JITPCB_BIN_PREFIX = $(JITPCB_ROOT)/
endif

ifdef JITPCB_DEBUG
JITPCB_BIN = $(JITPCB_BIN_PREFIX)jitpcb-debug
else
JITPCB_BIN = $(JITPCB_BIN_PREFIX)jitpcb
endif

# ====== Configuration Variables ===============================================

ifndef JITPCB_SEED
JITPCB_SEED = 0
endif

# ====== Generator Flow Variables ==============================================

LIB_DIR = $(JITPCB_SRC_ROOT)/lib
INPUT_DIR = $(JITPCB_SRC_ROOT)/inputs
BIN_DIR = bin

# Default JITPCB library Stanza files
LIB_ROOTS = footprints components symbols parts interfaces modules peripherals standalone-wrapper generator-utils
LIB_SRCS = $(addprefix $(LIB_DIR)/,$(addsuffix .stanza,$(LIB_ROOTS)))
GEN_SRCS = ../src/powergen/treegen.stanza  ../src/powergen/modulegen.stanza ../src/powergen/powergen.stanza ../src/powergen/csolver.stanza ../src/powergen/result-seq.stanza ../src/powergen/power-system-gen.stanza

# Uncomment this to add flags by default
GEN_FLAGS := $(GEN_FLAGS) 'no-drc'

# ====== Top-Level Targets ====================================================

# An empty rule for SUFFIXES removes all built-in rules (for c, o files, etc.)
.SUFFIXES:

# Helper functions for getting design name without processor suffix.
# If DESIGN is "system-design-nucleo", $(call remove-platform,DESIGN) returns
# "system-design"
empty :=
space := $(empty) $(empty)
join-with = $(subst $(space),$1,$(strip $2))
get-processor = $(lastword $(subst -, ,$1))
remove-processor = $(call join-with,-,$(filter-out $(call get-processor,$1),$(subst -, ,$1)))
name-root = $(firstword $(subst ., ,$1))

# ====== Concrete Targets =====================================================

# All following targets should not have intermediate files removed if a process fails
.SECONDARY:

# ====== Generator Targets ====================================================

$(BIN_DIR):
	mkdir -p ./$@

# # Special case to use stanza.build on current generator system
# $(BIN_DIR)/ayar-al7-host-generator: $(LIB_DIR)/ayar-al7-host-generator.stanza $(LIB_SRCS) | $(BIN_DIR)
# 	$(JITPCB_BIN) build ayar-al7-host-generator
# 	rm -rf $@.s

$(BIN_DIR)/%-generator: $(LIB_DIR)/%-generator.stanza $(LIB_SRCS) $(GEN_SRCS) | $(BIN_DIR) 
	$(JITPCB_BIN) $< $(LIB_SRCS) $(GEN_SRCS) -s $@.s -o $@
	rm -rf $@.s

TESTER_GENERATOR = $(BIN_DIR)/tester-generator
SYSTEM_GENERATOR = $(BIN_DIR)/system-generator

# ====== Input Spec Targets ===================================================

# Need empty rule to prevent infinite recursive prequisites
$(INPUT_DIR)/%-tester.ti: ;

# Second expansion is needed to resolve the pattern matches in function calls
.SECONDEXPANSION:

%-system.si: $(INPUT_DIR)/$$(call remove-processor,%)-system.si
	cp $< $@

# ====== Input Spec to ESIR Targets ============================================

%-system.prune-lower.esir: %-system.si $(SYSTEM_GENERATOR)
	$(SYSTEM_GENERATOR) -passes input lower prune -flags input = $< $(call get-processor,$*) $(GEN_FLAGS) -o $(call name-root,$@)

%-system.solve-requirements.esir: %-system.si $(SYSTEM_GENERATOR)
	$(SYSTEM_GENERATOR) -passes input lower prune solve-requirements -flags input = $< $(call get-processor,$*) $(GEN_FLAGS) -o $(call name-root,$@)

%-system.kyn: %-system.si $(SYSTEM_GENERATOR)
	$(SYSTEM_GENERATOR) -passes input lower prune solve-requirements key-in -flags input = $< $(call get-processor,$*) $(GEN_FLAGS) -o $(call name-root,$@)

# ====== Generator to ESIR Targets =============================================

# Catch-all generator target. Use this to produce ESIR from any lib/*-generator.stanza file
%-standalone.prune-lower.esir: $(BIN_DIR)/%-generator
	$< -passes input lower prune -flags $(GEN_FLAGS) -o $(call name-root,$@)

%.clean:
	rm -rf ./$(call name-root,$@).* ./~$(call name-root,$@).* ./.tmp ./*.rte ./*.log
