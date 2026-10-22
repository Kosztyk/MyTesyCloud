# Publish MyTESY Cloud in HACS

1. Confirm HACS, Hassfest and packaging workflows pass on the preparation PR.
2. Merge to main and verify all checks pass there.
3. Publish v1.1.1 after successful main-branch validation. The release workflow is configured to perform this once.
4. Submit a PR to `hacs/default:master` adding `"Kosztyk/MyTesyCloud"` alphabetically in the `integration` file.
5. Include the published release URL and links to the passing HACS and Hassfest jobs. Tick every checklist item in the official HACS template.

Do not post unnecessary comments or duplicate PRs.
