import requests
import matplotlib.pyplot as plt
import numpy as np

GITHUB_USER = 'vaishcodescape'

# Fetch all public repos
def get_repos(user):
    repos = []
    page = 1
    while True:
        url = f'https://api.github.com/users/{user}/repos?per_page=100&page={page}'
        r = requests.get(url)
        data = r.json()
        if not data:
            break
        repos.extend([repo['name'] for repo in data])
        page += 1
    return repos

# Fetch activity stats
def get_activity(user, repos):
    stats = {
        'Commits': 0,
        'Pull requests': 0,
        'Issues': 0,
        'Code review': 0
    }
    headers = {'Accept': 'application/vnd.github.v3+json'}
    for repo in repos:
        # Commits
        commits_url = f'https://api.github.com/repos/{user}/{repo}/commits?author={user}'
        commits = requests.get(commits_url, headers=headers).json()
        stats['Commits'] += len(commits) if isinstance(commits, list) else 0
        # PRs
        prs_url = f'https://api.github.com/repos/{user}/{repo}/pulls?state=all&per_page=100'
        prs = requests.get(prs_url, headers=headers).json()
        stats['Pull requests'] += len([pr for pr in prs if pr.get('user', {}).get('login') == user]) if isinstance(prs, list) else 0
        # Issues
        issues_url = f'https://api.github.com/repos/{user}/{repo}/issues?state=all&per_page=100'
        issues = requests.get(issues_url, headers=headers).json()
        stats['Issues'] += len([issue for issue in issues if issue.get('user', {}).get('login') == user and 'pull_request' not in issue]) if isinstance(issues, list) else 0
        # Code reviews (approximated by review comments on PRs)
        reviews_url = f'https://api.github.com/repos/{user}/{repo}/pulls?state=all&per_page=100'
        prs_for_reviews = requests.get(reviews_url, headers=headers).json()
        for pr in prs_for_reviews if isinstance(prs_for_reviews, list) else []:
            pr_number = pr.get('number')
            reviews_api = f'https://api.github.com/repos/{user}/{repo}/pulls/{pr_number}/reviews'
            reviews = requests.get(reviews_api, headers=headers).json()
            stats['Code review'] += len([review for review in reviews if review.get('user', {}).get('login') == user]) if isinstance(reviews, list) else 0
    return stats

def plot_radar(stats):
    labels = list(stats.keys())
    values = list(stats.values())
    total = sum(values)
    if total == 0:
        values = [1 for _ in values]  # Avoid division by zero
        total = len(values)
    percentages = [v / total * 100 for v in values]
    labels = [f'{int(p)}%\n{l}' for p, l in zip(percentages, labels)]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    plt.figure(figsize=(6, 6), facecolor='#181c23')
    ax = plt.subplot(111, polar=True, facecolor='#181c23')
    ax.plot(angles, values, 'o-', linewidth=2, color='#39ff14')
    ax.fill(angles, values, alpha=0.25, color='#39ff14')
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, color='#b0b7c3')
    ax.set_yticklabels([])
    ax.spines['polar'].set_color('#39ff14')
    plt.tight_layout()
    plt.savefig('activity.png', bbox_inches='tight', facecolor='#181c23')
    plt.close()

def main():
    repos = get_repos(GITHUB_USER)
    stats = get_activity(GITHUB_USER, repos)
    plot_radar(stats)

if __name__ == '__main__':
    main() 