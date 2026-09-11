from vpc.base import Base

class Rest(Base):
    def get_vpc(self, vpc_name):
        """
        Get KubeOVN VPC details

        Args:
            vpc_name: Name of KubeOVN VPC

        Returns:
            dict: VPC object or None if not found
        """
        pass
