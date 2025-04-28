#!/usr/bin/env python3

import aws_cdk as cdk

from wd_siem.wd_siem_stack import WdSiemStack


app = cdk.App()
WdSiemStack(app, "wd-siem")

app.synth()
