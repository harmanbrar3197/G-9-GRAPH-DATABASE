#!/usr/bin/env python3
"""Generate reproducible synthetic users/friendships CSV files (seed=9)."""
import csv, random

def generate(n=100, edges_per_user=4, seed=9):
    rng=random.Random(seed)
    users=[(i, f"User_{i}") for i in range(1,n+1)]
    edges=set()
    for i in range(1,n+1):
        for _ in range(edges_per_user):
            j=rng.randint(1,n)
            if i != j: edges.add(tuple(sorted((i,j))))
    with open("dataset/users.csv", "w", newline="") as f:
        w=csv.writer(f); w.writerow(["id","name"]); w.writerows(users)
    with open("dataset/friendships.csv", "w", newline="") as f:
        w=csv.writer(f); w.writerow(["user_a","user_b"]); w.writerows(sorted(edges))
    print(f"Generated {len(users)} users and {len(edges)} unique friendships.")

if __name__ == "__main__": generate()
