# Security Policy

## Supported releases

DEAPack provides security fixes for the newest stable 2.x release. Before a
stable 2.x release exists, the newest public 2.x prerelease is supported until
it is superseded. Historical 0.1.x releases, superseded prereleases, arbitrary
development commits, and third-party forks are not maintained security lines.

Security support does not turn a prerelease into a stable API commitment. A
scientific-correctness issue that can cause DEAPack to certify or publish an
invalid result is treated as a security-sensitive integrity report even when
it does not involve code execution or data disclosure.

## Report a vulnerability privately

Use GitHub's
[private vulnerability reporting form](https://github.com/daopingw/DEAPack/security/advisories/new).
Do not disclose vulnerability details in a public issue, discussion, pull
request, or benchmark report.

If the private form is unavailable, open a public issue containing no
vulnerability details and ask the maintainers to enable private reporting.
Wait for a private channel before sharing a proof of concept, affected data,
or exploit details. The project intentionally does not publish an unconfirmed
security email address.

A useful private report includes:

- the affected DEAPack version or full commit hash;
- the operating system, Python version, and installation source;
- the affected API, model, parser, archive, or release path;
- the security or scientific-integrity impact;
- minimal reproduction steps and, when safe, a proof of concept;
- any known workaround or proposed remediation; and
- disclosure constraints or a preferred credit name, if applicable.

Maintainers will assess the report privately, coordinate remediation and
disclosure with the reporter, and publish an advisory when users need to take
action. No response or resolution deadline is promised before the project has
documented maintainer coverage for that release line.

## Public correctness reports

Ordinary numerical discrepancies, documentation errors, feature requests, and
performance regressions can use the public issue tracker when they do not
expose confidential data, an exploitable trust-boundary failure, or a way to
publish an uncertified result as certified. When uncertain, use private
vulnerability reporting first.
