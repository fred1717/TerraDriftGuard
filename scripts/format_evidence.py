"""
format_evidence.py

Reads a Step Functions execution JSON from stdin and writes
a readable plain-text report to stdout.

Usage (from TerraDriftGuard/):
    aws stepfunctions describe-execution \
        --execution-arn $EXEC_ARN \
        --output json --no-cli-pager \
        | python3 scripts/format_evidence.py \
        > evidence/cli/sg_open_ssh.txt
"""

import json
import sys


def main():
    raw = json.load(sys.stdin)
    for key in ('input', 'output'):
        if key in raw and isinstance(raw[key], str):
            raw[key] = json.loads(raw[key])

    o = raw['output']
    n = o['normalized']
    e = o['enriched']
    r = o['remediation']['plan']
    t = o['terraform']
    esc = o['escalation']

    lines = []
    lines.append('EXECUTION: ' + raw['name'])
    lines.append('STATUS:    ' + raw['status'])
    lines.append('STARTED:   ' + str(raw['startDate']))
    lines.append('STOPPED:   ' + str(raw['stopDate']))
    lines.append('')
    lines.append('--- INPUT EVENT ---')
    lines.append('Resource:    ' + n['resourceId'])
    lines.append('Type:        ' + n['resourceType'])
    lines.append('Config Rule: ' + n['configRuleName'])
    lines.append('Region:      ' + n['region'])
    lines.append('Severity:    ' + n['severity'])
    lines.append('Annotation:  ' + n['annotation'])
    lines.append('Previous:    ' + n['previousCompliance'])
    lines.append('Detected At: ' + n['detectedAt'])
    lines.append('')
    lines.append('--- ENRICHMENT ---')
    lines.append('Config Status:   ' + e['currentConfig'].get('status', 'OK'))
    lines.append('Prior Incidents: ' + str(e['historyCount']))
    lines.append('')
    lines.append('--- BEDROCK ANALYSIS ---')
    lines.append('SUMMARY:')
    lines.append(r['SUMMARY'])
    lines.append('')
    lines.append('RISK ASSESSMENT:')
    lines.append(r['RISK_ASSESSMENT'])
    lines.append('')
    lines.append('LIKELY CAUSE:')
    lines.append(r['LIKELY_CAUSE'])
    lines.append('')
    lines.append('REMEDIATION:')
    lines.append(r['REMEDIATION'])
    lines.append('')
    lines.append('--- TERRAFORM SNIPPET ---')
    lines.append(r['TERRAFORM_SNIPPET'])
    lines.append('')
    lines.append('--- GENERATED TERRAFORM FILE ---')
    lines.append(t['terraformFile'])
    lines.append('')
    lines.append('--- ESCALATION ---')
    lines.append('PR URL:   ' + esc['pr_url'])
    lines.append('Branch:   ' + esc['branch'])
    lines.append('Filename: ' + esc['filename'])
    lines.append('SNS Sent: ' + str(esc['notification_sent']))

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
