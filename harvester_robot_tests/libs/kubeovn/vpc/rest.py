from vpc.base import Base


class Rest(Base):
    def get_vpc(self, vpc_name):
        """
        Get KubeOVN VPC details

        Args:
            vpc_name: Name of KubeOVN VPC

        Returns:
            dict: KubeOVN VPC object or None if not found
        """
        pass

    def create_vpc(self, vpc_name, **kwargs):
        """
        Create new KubeOVN VPC

        Args:
            vpc_name: Name of KubeOVN VPC

        Returns:
            dict: KubeOVN VPC Object or None if not found
        """
        pass

    def delete_vpc(self, vpc_name):
        """
        Delete KubeOVN VPC

        Args:
            vpc_name: Name of KubeOVN VPC to be deleted

        Returns
            dict: The deleted KubeOVN VPC
        """
        pass
