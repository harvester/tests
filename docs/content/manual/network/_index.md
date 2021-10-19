---
title: Network
---
All of the network tests mostly boil down to getting an external VLAN setup and testing connectivity

To add a VLAN to a cluster you need to add a network first. You do this in settings by enabling the VLAN setting for network and specifying a network interface. You can then create multiple networks with multiple VLANs. You will also want to add a public SSH key to test SSH connectivity. If SSH connectivity isn't feasible to test in automation we could substitute this with a basic nginx config and just do a get request on port 80. It's really just making sure that it can handle a multi-stage handshake.
At some point we should test with multiple external VLANs, but currently we don't have that set up in any of the testing environments