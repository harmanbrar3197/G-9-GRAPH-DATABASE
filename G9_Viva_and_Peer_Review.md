# G9: viva preparation and peer-review template

## Part A. Viva questions (every member must answer all of them)
Answers should come from your own paper and measurements. Hints only.

1. What is index-free adjacency, and why does it matter for traversals? (Section II-B, RQ2)
2. How does a recursive CTE execute in PostgreSQL? What are the working table and UNION vs UNION ALL? (II-C)
3. Why store both directions of each friendship in both systems? (IV-A)
4. Why does the PostgreSQL query end with count(DISTINCT id)? What does UNION actually de-duplicate? (IV-B)
5. Cypher variable-length patterns enumerate paths. How did you check that Neo4j did not blow up, and what did PROFILE show? (IV-B, VI-D)
6. Which indexes did you create in each system and why? What would happen without them? (IV-F)
7. Why sample start users by degree? What happens if you pick only low-degree users? (V, Fig. 5)
8. What is the difference between cold and warm runs and how did you produce each? (IV-D)
9. Explain one result in your Table IV using the EXPLAIN ANALYZE or PROFILE output. (VI-D)
10. Which of your expectations E1 to E3 held, and which did not? (VI-C)
11. Property graph vs RDF: give one difference and one query-language example. (VI-A, Table VI)
12. Name three threats to validity and one mitigation each. (VI-F)
13. What is your research gap and which papers support it? (III-D)
14. When would you still choose PostgreSQL over Neo4j? (VI-E)
15. Who wrote which part, and can you explain a section written by someone else? (contribution statement)

## Part B. Peer-review form (for the group you are assigned)
Reviewer group: ____  Reviewed group/topic: ____

| Criterion | Rating (1-5) | Specific comments (quote a section, figure or table) |
|---|---|---|
| Problem and three research questions are clear and answerable | | |
| Literature review is grouped by theme, recent, with a clear gap | | |
| Method and code are reproducible (repository, README, versions) | | |
| Results answer RQ1 to RQ3 with data; graphs labelled; reasons explained | | |
| Writing, IEEE format and citations | | |

Three strengths (specific): 1. ____ 2. ____ 3. ____
Three improvements (specific, actionable): 1. ____ 2. ____ 3. ____
One question you would ask in the viva: ____
Avoid generic one-line comments; the rubric awards marks for specific, constructive reviews.

## Part C. Plagiarism check steps (S4)
1. Export the final PDF. 2. Upload to Turnitin or DrillBit as your institute requires.
3. Exclude the reference list in the settings. 4. Target similarity below 10%.
5. Rewrite any matched passages in your own words and cite; do not just reword the matched text superficially.
6. Attach the report to the submission.
