feature: Graviton support for PyTorch and Tensorflow frameworks

*Issue #, if available:*

*Description of changes:*
Added the necessary changes to incorporate the [Graviton instances](https://github.com/aws/deep-learning-containers/releases/tag/v1.0-pt-graviton-sagemaker-1.12.1-inf-cpu-py38) into the `PyTorch` and `Tensorflow` frameworks.

*Testing done:*
Locally tested the feature to extract image string with the following code, where the output should match with expected DLC image URI's for PyTorch
(`763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference-graviton:1.12.1-cpu-py38-ubuntu20.04-sagemaker`) 
and Tensorflow
(`763104351884.dkr.ecr.us-west-2.amazonaws.com/tensorflow-inference-graviton:2.9.1-cpu-py38-ubuntu20.04-sagemaker`).

```bash
>>> sagemaker.image_uris.retrieve("pytorch","us-west-2", instance_type="ml.c6g.4xlarge")
'763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference-graviton:1.12.1-cpu-py38-ubuntu20.04-sagemaker'

>>> sagemaker.image_uris.retrieve("tensorflow","us-west-2", instance_type="ml.t4g.2xlarge")
'763104351884.dkr.ecr.us-west-2.amazonaws.com/tensorflow-inference-graviton:2.9.1-cpu-py38-ubuntu20.04-sagemaker'

```

## Merge Checklist

_Put an `x` in the boxes that apply. You can also fill these out after creating the PR. If you're unsure about any of them, don't hesitate to ask. We're here to help! This is simply a reminder of what we are going to look for before merging your pull request._

#### General

- [x] I have read the [CONTRIBUTING](https://github.com/aws/sagemaker-python-sdk/blob/master/CONTRIBUTING.md) doc
- [x] I certify that the changes I am introducing will be backward compatible, and I have discussed concerns about this, if any, with the Python SDK team
- [x] I used the commit message format described in [CONTRIBUTING](https://github.com/aws/sagemaker-python-sdk/blob/master/CONTRIBUTING.md#committing-your-change)
- [ ] I have passed the region in to all S3 and STS clients that I've initialized as part of this change.
- [ ] I have updated any necessary documentation, including [READMEs](https://github.com/aws/sagemaker-python-sdk/blob/master/README.rst) and [API docs](https://github.com/aws/sagemaker-python-sdk/tree/master/doc) (if appropriate)

#### Tests

- [x] I have added tests that prove my fix is effective or that my feature works (if appropriate)
- [x] I have added unit and/or integration tests as appropriate to ensure backward compatibility of the changes
- [ ] I have checked that my tests are not configured for a specific region or account (if appropriate)
- [ ] I have used [`unique_name_from_base`](https://github.com/aws/sagemaker-python-sdk/blob/master/src/sagemaker/utils.py#L77) to create resource names in integ tests (if appropriate)

By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.
