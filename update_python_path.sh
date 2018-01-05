#!/bin/bash
sed -i.old '1 s|.*|#!'$1'|' cgi-bin/submit.py