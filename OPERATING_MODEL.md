# Operating Model: One Owner, AI Agents, One Delivery Path

One owner decides what to build and what to sell. AI agents do the engineering, review, and release preparation around those decisions. The owner does not need to read or review code, so every decision that matters is put to the owner in plain language, and only the steps that truly need a person wait for one.

This describes how the setup is meant to run. It makes no claim about results.

## One way of working

There are no operating modes. A question from the owner gets an answer and changes nothing; an instruction gets the work done. A question never pauses or cancels work the owner already approved, and an instruction counts in whichever thread the owner gave it. A stop from the owner always wins.

- **One thread talks to the owner.** The thread the owner writes in is the only one that asks the owner anything or reports to the owner. A thread started by an agent begins working at once on its brief, carries the authorization and limits of the thread that started it, and reports back to that thread; an owner-only need goes back there, and that thread brings it to the owner once with a recommendation. A scheduled thread reports only as its written procedure says.
- **Cloud work is pushed every turn.** A cloud thread that starts on its own side branch commits as it goes and pushes that branch before every turn ends, so no finished turn leaves work only on the cloud machine. It pushes more often only where a push starts no build. The default branch still moves only after review, and the side branch is deleted once the default branch holds the work.
- **`SUM.md` stays the discussion record.** Where the goal, scope, or intended experience is unresolved, the owner and an agent align one point at a time and record the owner's exact words, the agreed points, and the open questions in the project's root `SUM.md`, newest first. Agreements recorded there carry into new sessions.

## Roles

| Role | Who | Does |
| --- | --- | --- |
| Owner | A person | Decides what to build and for which marketplace, approves the owner gates below, does the security steps only a human can do, and tests finished features |
| Builder | A coding agent | Makes routine implementation decisions, does the work, validates it, and commits it |
| Reviewer | A coding agent in a fresh context, never the builder | Checks each committed change against the request and returns In Spec or Out Of Spec with evidence |
| Helpers | Other agents, as needed | Research or parallel work for the builder; a helper works under the authorization and limits of the agent that sent it and reports to it |

## How one change ships

1. Where the goal, scope, or intended experience is unresolved, the owner and an agent align one point at a time and record the agreement in `SUM.md`.
2. Once the objective is clear, the builder works on the default branch, runs the checks the change and its real risks need, inspects the result, and commits with a plain-language message.
3. A fresh reviewer checks that full commit. On Out Of Spec, the builder fixes the findings and the new commit is reviewed again, with no round limit.
4. On In Spec, the builder pushes straight to the default branch. There are no routine pull requests, no auto-merge, and no standing watchers; a deployment the push triggers automatically is part of delivery. A pull request is used only where a task or repository requires one.
5. The builder refreshes the project's `BRIEFME.html` and continues any remaining authorized work.

## Records

- **The repository** holds the code, commits, checks, and results. No separate tracker cards or dispatch bots are required.
- **`BRIEFME.html`** is each project's visual brief for the owner and agents: what the project is, its goal, where it stands, and what comes next, with a short dated entry after each change.
- **`SUM.md`** is the discussion record: the owner's exact words with their date, the agreements, and the open questions.
- **Commit messages** say what changed for the user and what was checked.

## Gates

- **Review before push.** A push needs an In Spec verdict from a fresh reviewer on the final commit.
- **Checks.** A push needs the repository's relevant checks to pass where it has them.
- **Owner approval.** Spending, account changes, irreversible actions, external messages, publishing, trading, production deployment, publicly listing a product, ongoing monitoring, new recurring automation and security steps only a human can do (signing in, passwords, codes, approval prompts, credential or permission grants) require authorization covering that action. Authorized read-only account checks need no new approval, and an authorized push covers its automatic deployment. If authorization is missing, only that action waits with one plain sentence saying what the owner is approving. Security-related code that passes an independent In Spec review ships like any other change, without the owner's review.
- **Launch gates.** A product goes on sale only when every non-negotiable gate passes, each closed with its evidence. The weights add up to 100 and rank the gates by how much damage a failure would do. Anything at 10% or above must pass; a negotiable gate may stay open as a risk the owner knowingly accepted; and anything the target marketplace or the law requires is non-negotiable for that listing, whatever its weight. The sources for the first four are marketplace and advertising rules, checked October 2, 2026; the sources for the other five were read October 13, 2026:
  1. *A stranger completes the core task alone* (18%), with no help, no placeholder content, and no crash on that path. Apple App Review Guideline 2.1(a); Google Play's Functionality, Content, and User Experience policy.
  2. *Paying works* (15%), and the buyer receives what they paid for. Apple App Review Guideline 2.1(b).
  3. *Nothing breaks badly* (15%): no lost user data, and no personal data used, sent, or shared without permission. Apple App Review Guideline 5.1.2(i).
  4. *The listing is honest* (14%): title, description, and screenshots show only what the product does today. Apple App Review Guideline 2.3; Google Play's Metadata policy; FTC Act Section 5.
  5. *Privacy policy and account deletion* (10%). Apple and Google Play require both; Apple requires deletion only when the product has accounts.
  6. *Security check* (9%, negotiable).
  7. *Off switch* (7%, negotiable). GitHub describes being able to "disable changes in seconds without rolling back a deployment."
  8. *Watching for problems after launch* (6%, negotiable). Google: "Set up monitoring for your new service."
  9. *A way for buyers to reach the owner* (6%, negotiable). Atlassian: "Teams must build support processes… before it goes live."

Release happens in three stages: a private link for a few people while any non-negotiable gate fails, a priced listing once every non-negotiable gate passes, and an announcement only when the owner chooses, after the listing has earned sales.
