GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
ifeq ($(GIT_BRANCH),HEAD)
GIT_BRANCH := $(shell git describe --tags)
endif

GITHUB_REPO_FULL := $(shell git ls-remote --get-url $(GIT_REMOTE) 2>/dev/null |\
                      sed -e 's/^.*github\.com.//;s/\.git$$//')
CI_AUTHOR := CircleCI Job
export GIT_COMMITTER_NAME=”CircleCI job”
export GIT_COMMITTER_EMAIL=”noreply@github.com”


# Default to pushing if a key or token is available.
ifneq (,$(GH_TOKEN)$(CI_HAS_WRITE_KEY))
PUSH_GHPAGES ?= true
endif

PUSH_GHPAGES ?= false

.IGNORE: fetch-ghpages
.PHONY: fetch-ghpages
fetch-ghpages:
	@echo vars: $(PUSH_GHPAGES) $(SOURCE_BRANCH) $(GITHUB_REPO_FULL) $(GIT_BRANCH)
	git fetch -q origin gh-pages:gh-pages

GHPAGES_ROOT := /tmp/ghpages$(shell echo $$$$)

ghpages: $(GHPAGES_ROOT)

$(GHPAGES_ROOT): fetch-ghpages
	pwd
	@git show-ref refs/heads/gh-pages >/dev/null 2>&1 || \
	  (git show-ref refs/remotes/origin/gh-pages >/dev/null 2>&1 && \
	    git branch -t gh-pages origin/gh-pages) || \
	  ! echo 'Error: No gh-pages branch, run `make -f $(LIBDIR)/setup.mk setup-ghpages` to initialize it.'
	git clone -q -b gh-pages . $@

GHPAGES_TARGET := $(GHPAGES_ROOT)$(filter-out /master,/$(SOURCE_BRANCH))

ifneq ($(GHPAGES_TARGET),$(GHPAGES_ROOT))
$(GHPAGES_TARGET): $(GHPAGES_ROOT)
	mkdir -p $@
endif


ifneq ($(GHPAGES_TARGET),$(GHPAGES_ROOT))
GHPAGES_ALL += $(GHPAGES_ROOT)/$(GIT_BRANCH)/definitions.yaml
GHPAGES_ALL += $(GHPAGES_ROOT)/index.html
$(GHPAGES_ROOT)/$(GIT_BRANCH)/definitions.yaml: $(GHPAGES_ROOT)
	find . -name '*.yaml'
	git branch -a
	tox -e build
	mkdir -p $(GHPAGES_ROOT)/$(GIT_BRANCH)
	cp docs/definitions.yaml $@
	cp -rp other $(GHPAGES_ROOT)/$(GIT_BRANCH)

$(GHPAGES_ROOT)/index.html: $(GHPAGES_ROOT)/$(GIT_BRANCH)/definitions.yaml
	cp index.html $@
endif




cleanup-ghpages:
	pwd
	echo cleanup-ghpages

.PHONY: ghpages gh-pages
gh-pages: ghpages
ghpages: cleanup-ghpages $(GHPAGES_ALL)
	pwd
	git -C $(GHPAGES_ROOT) add -f $(GHPAGES_ALL)
	if test `git -C $(GHPAGES_ROOT) status --porcelain | grep '^[A-Z]' | wc -l` -gt 0; then \
	  git -C $(GHPAGES_ROOT)  commit --author "$(CI_AUTHOR) <noreply@circleci.com>" -m "Script updating gh-pages from $(shell git rev-parse --short HEAD). [ci skip]"; fi

ifeq (true,$(PUSH_GHPAGES))
ifneq (,$(if $(CI_HAS_WRITE_KEY),1,$(if $(GH_TOKEN),,1)))
	git -C $(GHPAGES_ROOT) push https://github.com/$(GITHUB_REPO_FULL) gh-pages
else
	@echo git -C $(GHPAGES_ROOT) push -q https://github.com/$(GITHUB_REPO_FULL) gh-pages
	@git -C $(GHPAGES_ROOT) push -q https://$(GH_TOKEN)@github.com/$(GITHUB_REPO_FULL) gh-pages # >/dev/null 2>&1
endif
else
	git -C $(GHPAGES_ROOT) push origin gh-pages
endif # PUSH_GHPAGES
	-rm -rf $(GHPAGES_ROOT)
