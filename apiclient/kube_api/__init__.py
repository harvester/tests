# Copyright (c) 2024 SUSE LLC

from .api import KubeAPI

# This is just to make `tox -e pep8` stop complaining
# about things that it really shouldn't complain about.
_ = KubeAPI
