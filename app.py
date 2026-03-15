#!/usr/bin/env python3
from aws_cdk import App
from stacks.mlops_stack import MLOpsStack

app = App()
MLOpsStack(app, 'MLOpsStack')
app.synth()
