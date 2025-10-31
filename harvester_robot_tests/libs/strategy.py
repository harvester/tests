from enum import Enum


class HarvesterOperationStrategy(Enum):
    REST = "rest"
    CRD = "crd"
