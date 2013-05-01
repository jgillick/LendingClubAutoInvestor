#!/usr/bin/env python

#
# Utilities used by the LendingClubInvestor
#

import re
from pybars import Compiler


def get_filter_json(filters):
    """"
    Given search filters, this function returns the JSON that
    LendingClub expects for it's investment search
    """
    compiler = Compiler()

    if not filters:
        return False

    tmpl_source = u"""
    [
        {
            "m_id": 39,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": "Year3",
                        "label": "36-month",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "Year5",
                        "label": "60-month",
                        "sqlValue": null,
                        "valueIndex": 1
                    }
                ],
                "m_type": "MVAL",
                "m_rep": "CHKBOX",
                "m_label": "Term (36 - 60 month)",
                "id": 39,
                "m_onHoverHelp": "Select the loan maturities you are interested to invest in",
                "m_className": "classname",
                "m_defaultValue": [
                    {
                        "value": "Year3",
                        "label": "36-month",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "Year5",
                        "label": "60-month",
                        "sqlValue": null,
                        "valueIndex": 1
                    }
                ]
            },
            "m_value": [
            {{#if term36month}}
                {
                    "value": "Year3",
                    "label": "36-month",
                    "sqlValue": null,
                    "valueIndex": 0
                },
            {{/if}}
            {{#if term60month}}
                {
                    "value": "Year5",
                    "label": "60-month",
                    "sqlValue": null,
                    "valueIndex": 1
                }
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {
            "m_id": 38,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": true,
                        "label": "Exclude loans invested in",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ],
                "m_type": "SVAL",
                "m_rep": "CHKBOX",
                "m_label": "Exclude Loans already invested in",
                "id": 38,
                "m_onHoverHelp": "Use this filter to exclude loans from a borrower that you have already invested in.",
                "m_className": "classname",
                "m_defaultValue": [
                    {
                        "value": true,
                        "label": "Exclude loans invested in",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ]
            },
            "m_value": [
            {{#if exclude_existing}}
                {
                    "value": true,
                    "label": "Exclude loans invested in",
                    "sqlValue": null,
                    "valueIndex": 0
                }
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {
            "m_id": 10,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": "All",
                        "label": "All",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "D",
                        "label": "<span class=\\"grades d-loan-grade\\">D</span> 18.76%",
                        "sqlValue": null,
                        "valueIndex": 1
                    },
                    {
                        "value": "A",
                        "label": "<span class=\\"grades a-loan-grade\\">A</span> 7.41%",
                        "sqlValue": null,
                        "valueIndex": 2
                    },
                    {
                        "value": "E",
                        "label": "<span class=\\"grades e-loan-grade\\">E</span> 21.49%",
                        "sqlValue": null,
                        "valueIndex": 3
                    },
                    {
                        "value": "B",
                        "label": "<span class=\\"grades b-loan-grade\\">B</span> 12.12%",
                        "sqlValue": null,
                        "valueIndex": 4
                    },
                    {
                        "value": "F",
                        "label": "<span class=\\"grades f-loan-grade\\">F</span> 23.49%",
                        "sqlValue": null,
                        "valueIndex": 5
                    },
                    {
                        "value": "C",
                        "label": "<span class=\\"grades c-loan-grade\\">C</span> 15.80%",
                        "sqlValue": null,
                        "valueIndex": 6
                    },
                    {
                        "value": "G",
                        "label": "<span class=\\"grades g-loan-grade\\">G</span> 24.84%",
                        "sqlValue": null,
                        "valueIndex": 7
                    }
                ],
                "m_type": "MVAL",
                "m_rep": "CHKBOX",
                "m_label": "Interest Rate",
                "id": 10,
                "m_onHoverHelp": "Specify the interest rate ranges of the notes  you are willing to invest in.",
                "m_className": "short",
                "m_defaultValue": [
                    {
                        "value": "All",
                        "label": "All",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ]
            },
            "m_value": [
            {{#if grades.All }}
                {
                    "value": "All",
                    "label": "All",
                    "sqlValue": null,
                    "valueIndex": 0
                }
            {{else}}
                {{#if grades.D}}
                {
                    "value": "D",
                    "label": "<span class=\\"grades d-loan-grade\\">D</span> 18.76%",
                    "sqlValue": null,
                    "valueIndex": 1
                },
                {{/if}}
                {{#if grades.A}}
                {
                    "value": "A",
                    "label": "<span class=\\"grades a-loan-grade\\">A</span> 7.41%",
                    "sqlValue": null,
                    "valueIndex": 2
                },
                {{/if}}
                {{#if grades.E}}
                {
                    "value": "E",
                    "label": "<span class=\\"grades e-loan-grade\\">E</span> 21.49%",
                    "sqlValue": null,
                    "valueIndex": 3
                },
                {{/if}}
                {{#if grades.B}}
                {
                    "value": "B",
                    "label": "<span class=\\"grades b-loan-grade\\">B</span> 12.12%",
                    "sqlValue": null,
                    "valueIndex": 4
                },
                {{/if}}
                {{#if grades.F}}
                {
                    "value": "F",
                    "label": "<span class=\\"grades f-loan-grade\\">F</span> 23.49%",
                    "sqlValue": null,
                    "valueIndex": 5
                },
                {{/if}}
                {{#if grades.C}}
                {
                    "value": "C",
                    "label": "<span class=\\"grades c-loan-grade\\">C</span> 15.80%",
                    "sqlValue": null,
                    "valueIndex": 6
                },
                {{/if}}
                {{#if grades.G}}
                {
                    "value": "G",
                    "label": "<span class=\\"grades g-loan-grade\\">G</span> 24.84%",
                    "sqlValue": null,
                    "valueIndex": 7
                }
                {{/if}}
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {
            "m_id": 37,
            "m_metadata": {
                "m_controlValues": null,
                "m_type": "SVAL",
                "m_rep": "TEXTBOX",
                "m_label": "Keyword",
                "id": 37,
                "m_onHoverHelp": "Type any keyword",
                "m_className": "classname",
                "m_defaultValue": []
            },
            "m_value": null,
            "m_visible": false,
            "m_position": 0
        }
    ]
    """

    template = compiler.compile(tmpl_source)
    out = template(filters)
    if not out:
        return False
    out = ''.join(out)

    # remove extra spaces
    out = re.sub('\n', '', out)
    out = re.sub('\s{3,}', ' ', out)

    # Remove hanging commas i.e: [1, 2,]
    out = re.sub(',\s*([}\\]])', '\\1', out)

    # Space between brackets i.e: ],  [
    out = re.sub('([{\\[}\\]])(,?)\s*([{\\[}\\]])', '\\1\\2\\3', out)

    # Cleanup spaces around [, {, }, ], : and , characters
    out = re.sub('\s*([{\\[\\]}:,])\s*', '\\1', out)

    return out
