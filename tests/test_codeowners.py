from atlas.codeowners import owners_for_fact, owners_for_path, parse_codeowners

SAMPLE = """
# comment line, ignored
* @default-owner
/facts/security-* @security-team
/facts/billing-* @billing-team @finance-lead
"""


def test_parse_ignores_comments_and_blank_lines():
    rules = parse_codeowners(SAMPLE)
    assert len(rules) == 3


def test_last_match_wins():
    rules = parse_codeowners(SAMPLE)
    # matches both "*" and "/facts/security-*" -- the more specific,
    # later rule should win per CODEOWNERS semantics
    owners = owners_for_path(rules, "facts/security-auth.md")
    assert owners == ["@security-team"]


def test_falls_back_to_default_owner():
    rules = parse_codeowners(SAMPLE)
    owners = owners_for_path(rules, "facts/reporting-module.md")
    assert owners == ["@default-owner"]


def test_multiple_owners():
    rules = parse_codeowners(SAMPLE)
    owners = owners_for_path(rules, "facts/billing-invoice.md")
    assert owners == ["@billing-team", "@finance-lead"]


def test_owners_for_fact_maps_subject_to_synthetic_path():
    rules = parse_codeowners(SAMPLE)
    owners = owners_for_fact(rules, fact_subject="security-token-rotation")
    assert owners == ["@security-team"]


def test_malformed_line_with_no_owners_is_skipped():
    # A pattern with no owner listed isn't valid CODEOWNERS syntax --
    # must be silently skipped, not crash or produce an empty-owners rule.
    rules = parse_codeowners("/facts/orphaned-*\n* @default-owner\n")
    assert rules == [("*", ["@default-owner"])]
