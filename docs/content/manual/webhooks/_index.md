---
title: Webhooks
---
**Note**: all the informations provided here are extraced from https://github.com/harvester/harvester/pull/919.

- (1) The user can issue requests to Harvester backend and (2) the backend translates the requests to kube-api .
- (3) The user can also send requests to kube-api directly. e.g., applying a manifest.
- Inside kube-api
    - (4) The mutating controller sends mutating requests to the webhook server (if any resource needs a field mutation).
    - (5) The validating controller sends validating requests to the webhook server (we can do field validating here).

## Limitations and changes:
- Error messages returned by the kube-api server are not under our control.
- The string "can't delete self" is what we can program in the webhook server.
- Extra actions are not supported. For example, we allow passing a removedDisks query parameter in a virtual machine deleting request.
    This is handy for GUI. But it can't be done in webhook server because the field is not defined in the CR.

## Test Plan
- Check pods. By default, there should be 3 pods:
```
$ kubectl get pods -n harvester-system -l app.kubernetes.io/component=webhook-server
NAME                                 READY   STATUS    RESTARTS   AGE
harvester-webhook-56c5998ff4-7t2zk   1/1     Running   0          2m46s
harvester-webhook-56c5998ff4-hn478   1/1     Running   0          2m46s
harvester-webhook-56c5998ff4-tcqg2   1/1     Running   0          2m47s

```
- Check service
```
$ kubectl get service harvester-webhook -n harvester-system
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
harvester-webhook   ClusterIP   10.53.140.127   <none>        443/TCP   4m27s
```
- Check ValidatingWebhookConfiguration and MutatingWebhookConfiguration configurations are created. These registrations tell what resources and what kind of operations on the resources need to be checked in mutating or validating webhooks.
```
$ kubectl get ValidatingWebhookConfiguration harvester-validator
NAME                  WEBHOOKS   AGE
harvester-validator   1          5m11s
```
```
$ kubectl get MutatingWebhookConfiguration harvester-mutator
NAME                WEBHOOKS   AGE
harvester-mutator   1          5m39s
```