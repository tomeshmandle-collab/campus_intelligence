# Git Workflow

## 1. Purpose

This guide explains how the CAI Campus Intelligence team should collaborate using Git and GitHub.

It is written for contributors who may be new to Git. The goal is a simple workflow that keeps the shared project stable while people work on separate tasks.

## 2. The basic idea

Git tracks changes to files. GitHub hosts the shared repository and adds collaboration tools such as issues and pull requests.

| Term | Meaning |
|---|---|
| Repository | The project folder and its tracked history |
| Working tree | The files currently on your computer |
| Stage | Select changes to include in the next commit |
| Commit | A saved snapshot of staged changes |
| Branch | A separate line of work |
| Push | Send local commits to the remote repository |
| Pull | Bring remote changes into the local branch |
| Pull request (PR) | Ask the team to review and merge a branch |
| Merge | Combine one branch's changes into another |
| Conflict | A change Git cannot combine automatically |

A commit is not the same as a push:
- **Commit** saves a snapshot in your local Git history.
- **Push** uploads your commits to GitHub.

## 3. Branch model

Use the repository's existing default branch. Do not rename `main`/`master` or create a new branching model without the Project Lead's approval.

Recommended approach:
- The default branch should contain integrated, reasonably stable work.
- Each task gets a short-lived feature or fix branch.
- Contributors open pull requests to merge work into the default branch.
- Avoid committing directly to the shared default branch for normal feature work.

Example branch names:
- `feature/notice-upload`
- `feature/public-notice-list`
- `feature/search-api`
- `fix/upload-validation`
- `docs/local-setup`

Use lowercase words separated by hyphens.

## 4. Before starting a task

1. Open the GitHub issue.
2. Confirm the goal, owner, dependencies, and acceptance criteria.
3. Check that the issue is not blocked.
4. Make sure your local repository is in a known state.
5. Update your local default branch.
6. Create a branch for the task.

Typical commands:

```bash
git status
git switch <default-branch>
git pull
git switch -c feature/short-task-name
```

Replace `<default-branch>` with the actual branch name used by the repository.

If your Git version does not support `git switch`, use the equivalent `git checkout` commands already familiar to the team.

## 5. While working

- Work only on the issue's scope.
- Save changes in small, meaningful commits.
- Do not include unrelated formatting or generated files.
- Check `git status` regularly.
- Pull the latest shared changes when appropriate, especially before opening a PR.
- If a shared API, schema, or status value needs to change, coordinate first.

Useful commands:

```bash
git status
git diff
git diff --staged
```

These help you see which files changed and what the changes contain.

## 6. Stage and commit

### Stage selected files

```bash
git add path/to/file
```

Or stage all current changes only after checking them:

```bash
git add .
```

### Review what is staged

```bash
git diff --staged
```

### Commit

```bash
git commit -m "feat: add notice upload validation"
```

Suggested commit prefixes:

| Prefix | Use |
|---|---|
| `feat:` | New functionality |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `test:` | Tests or test data |
| `refactor:` | Code restructuring without intended behaviour change |
| `chore:` | Maintenance or configuration |

Examples:
- `feat: add public notice detail view`
- `fix: reject unsupported upload files`
- `test: cover uploader access rules`
- `docs: clarify local setup`

A good commit message describes the change, not the amount of effort.

## 7. Push your branch

```bash
git push -u origin feature/short-task-name
```

The `-u` option links the local branch to its remote branch for convenient future pushes.

After the first push, the branch can usually be updated with:

```bash
git push
```

Pushing does not merge your changes into the default branch.

## 8. Open a pull request

On GitHub:

1. Open the repository.
2. Select the option to create a pull request for your pushed branch.
3. Set the base to the repository's agreed default branch.
4. Set the compare branch to your task branch.
5. Add a clear title and description.
6. Link the issue (for example, `Closes #12` if the actual issue number is 12).
7. Explain how you tested the change.
8. Mention any limitations or follow-up work.
9. Request the appropriate reviewer.

Do not invent issue numbers. Link the real issue created in the repository.

### Pull request description template

```markdown
## What changed
- 

## Why
- 

## How it was tested
- [ ] Automated tests
- [ ] Manual verification
- [ ] Not run (explain why)

## Screenshots or evidence
Add screenshots, logs, or a short demo where useful.

## Risks / follow-up
- 

Closes #
```

## 9. Review and merge

The reviewer should check:
- Does the change solve the issue?
- Is it limited to the intended scope?
- Does it follow project conventions?
- Are errors and edge cases handled?
- Were relevant tests run?
- Does it change a shared contract?
- Are there any security or data-exposure concerns?

The Project Lead should review changes involving:
- backend architecture;
- database schema or migrations;
- API contracts;
- authentication and authorization;
- file storage;
- OCR/AI processing;
- publication and withdrawal rules;
- deployment or secrets.

After required checks and review pass, merge using the repository's configured merge method. Avoid deleting or rewriting shared history.

## 10. Keep your branch up to date

If the default branch has moved ahead, bring those changes into your branch using the team's agreed approach.

A simple merge-based approach:

```bash
git switch <default-branch>
git pull
git switch feature/short-task-name
git merge <default-branch>
```

Resolve any conflicts, run relevant tests, then push the updated branch.

Do not use force-push on a shared branch. If a force-push seems necessary, ask the Project Lead first.

## 11. Merge conflicts

A conflict means Git needs a human to decide how two sets of edits should fit together.

Safe process:

1. Stop and read the conflict markers.
2. Understand both changes before editing.
3. Keep the intended behaviour from each side where possible.
4. Ask the relevant owner if the correct result is unclear.
5. Remove conflict markers after resolving.
6. Run tests and inspect the final diff.
7. Stage the resolved files and complete the merge.

Do not blindly choose “ours” or “theirs” for an entire file unless you understand the impact.

## 12. Common mistakes

### “I committed, but GitHub does not show my changes.”
You committed locally but have not pushed.

### “I pushed, but the default branch has not changed.”
You pushed a branch. Open a pull request and merge it after review.

### “My commit includes unrelated files.”
Inspect `git status` and `git diff --staged` before committing. Unstage unrelated files with:

```bash
git restore --staged path/to/file
```

### “I edited the wrong branch.”
Stop before committing more changes. Check `git status` and ask for help if you are unsure how to move the work safely.

### “I want to undo a commit already shared with others.”
Prefer a new corrective commit or `git revert` rather than rewriting shared history.

## 13. Rules for this project

- Every substantial task should map to a GitHub issue or a clear instruction from the Project Lead.
- Use one branch per task or closely related small set of changes.
- Keep pull requests focused and reviewable.
- Do not commit secrets, local databases, temporary uploads, or machine-specific configuration.
- Do not change the default branch or repository settings without coordination.
- Do not merge changes that break the agreed API or database contract.
- If a contract must change, update the documentation and notify dependent owners.
- Keep the branch history understandable; do not optimize for a perfect-looking history at the cost of losing work.

## 14. Minimum workflow checklist

- [ ] I understand the issue and its acceptance criteria.
- [ ] I updated the correct default branch.
- [ ] I created a task branch.
- [ ] I checked the files I changed.
- [ ] I staged only relevant files.
- [ ] I wrote a meaningful commit message.
- [ ] I pushed the branch.
- [ ] I opened a PR and linked the issue.
- [ ] I explained how I tested the change.
- [ ] I responded to review feedback.
- [ ] The PR was merged only after checks and review.
