#!/usr/bin/env python3
"""
Génère data/predictions.json et data/standings.json
Lancé quotidiennement par GitHub Actions — pas de limite CORS, clé API en secret.
"""
import json, math, os, re, unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
LEAGUES = {
    'fra.1': {'name': 'Ligue 1',        'fdCode': 'F1',  'ofCode': 'fr.1', 'mdTotal': 34},
    'esp.1': {'name': 'La Liga',        'fdCode': 'SP1', 'ofCode': 'es.1', 'mdTotal': 38},
    'eng.1': {'name': 'Premier League', 'fdCode': 'E0',  'ofCode': 'en.1', 'mdTotal': 38},
}

AF_KEY = os.environ.get('API_FOOTBALL_KEY', '')
DECAY_HALF_LIFE = 365  # jours

TEAM_ALIASES = {
    'psg':'parissaintgermain','paris':'parissaintgermain','parissg':'parissaintgermain',
    'ol':'olympiquelyonnais','lyon':'olympiquelyonnais',
    'om':'olympiquemarseille','marseille':'olympiquemarseille',
    'asmonaco':'monaco','lillelosc':'lille','losc':'lille',
    'stadederennais':'rennes','ognice':'nice','racingclubdelens':'lens',
    'racingstrasbourg':'strasbourg',
    'realmadridcf':'realmadrid','realmad':'realmadrid',
    'barca':'barcelona','fcbarcelona':'barcelona',
    'atlmadrid':'atleticomadrid','atletico':'atleticomadrid','atmadrid':'atleticomadrid',
    'athletic':'athleticclub','athleticbilbao':'athleticclub',
    'sociedad':'realsociedad','betis':'realbetis',
    'celta':'celtavigo','celtade':'celtavigo',
    'manutd':'manchesterunited','mufc':'manchesterunited','manunited':'manchesterunited',
    'mancity':'manchestercity','mcfc':'manchestercity',
    'spurs':'tottenham','tottenhamhotspur':'tottenham',
    'wolves':'wolverhampton','wolverhamptonwanderers':'wolverhampton',
    'newcastleunited':'newcastle','westhamunited':'westham',
    'brightonhovealbion':'brighton','nottmforest':'nottinghamforest',
    'sheffieldutd':'sheffieldunited','leedsunited':'leeds',
    'leicestercity':'leicester',
}

# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------
def normalize(name):
    name = name.lower()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'\b(fc|cf|ac|afc|sc|club|1)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name).strip()

def team_key(name):
    n = normalize(name)
    return TEAM_ALIASES.get(n, n)

def decay(date_str):
    try:
        d = datetime.fromisoformat(date_str[:10])
        return 0.5 ** ((datetime.utcnow() - d).days / DECAY_HALF_LIFE)
    except Exception:
        return 1.0

def poisson(lam, k):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

# ---------------------------------------------------------------------------
# Modèle Dixon-Coles
# ---------------------------------------------------------------------------
def dc_match(lh, la, rho=-0.1):
    MAX = 8
    ph = pd = pa = 0.0
    best = (0, 0, 0.0)
    for i in range(MAX + 1):
        for j in range(MAX + 1):
            if   i == 0 and j == 0: tau = 1 - lh * la * rho
            elif i == 0 and j == 1: tau = 1 + lh * rho
            elif i == 1 and j == 0: tau = 1 + la * rho
            elif i == 1 and j == 1: tau = 1 - rho
            else:                   tau = 1.0
            p = tau * poisson(lh, i) * poisson(la, j)
            if i > j:  ph += p
            elif i == j: pd += p
            else:      pa += p
            if p > best[2]: best = (i, j, p)
    t = ph + pd + pa
    return {'home': ph/t, 'draw': pd/t, 'away': pa/t,
            'score': f'{best[0]}-{best[1]}', 'lh': lh, 'la': la}

def derived(lh, la):
    MAX = 8
    p_under = sum(
        poisson(lh, i) * poisson(la, j)
        for i in range(MAX+1) for j in range(MAX+1) if i+j <= 2
    )
    btts = (1 - poisson(lh, 0)) * (1 - poisson(la, 0))
    ht_h, ht_a = lh * 0.475, la * 0.475
    hb = max(((i, j, poisson(ht_h, i)*poisson(ht_a, j)) for i in range(5) for j in range(5)),
             key=lambda x: x[2])
    return {'ou25': 1 - p_under, 'btts': btts, 'htScore': f'{hb[0]}-{hb[1]}', 'htProb': round(hb[2]*100)}

def elo_probs(rh, ra, home_adv=65):
    diff = (rh + home_adv) - ra
    p_half = 1 / (1 + 10 ** (-diff / 400))
    pd = 0.28 * math.exp(-((diff / 220) ** 2))
    remain = 1 - pd
    return {'home': remain * p_half, 'draw': pd, 'away': remain * (1 - p_half)}

# ---------------------------------------------------------------------------
# Calcul des forces + Elo
# ---------------------------------------------------------------------------
def compute_strengths(matches):
    tw = th = ta = 0.0
    for m in matches:
        w = decay(m['date'])
        tw += w; th += m['h'] * w; ta += m['a'] * w
    avg_h = th / tw if tw else 1.5
    avg_a = ta / tw if tw else 1.15

    stats = {}
    for m in matches:
        w = decay(m['date'])
        k1, k2 = team_key(m['team1']), team_key(m['team2'])
        for k in (k1, k2):
            if k not in stats:
                stats[k] = dict(hg=0,ha=0,ag=0,aa=0,wh=0,wa=0,n=0)
        s1, s2 = stats[k1], stats[k2]
        s1['hg'] += m['h']*w; s1['ha'] += m['a']*w; s1['wh'] += w; s1['n'] += 1
        s2['ag'] += m['a']*w; s2['aa'] += m['h']*w; s2['wa'] += w; s2['n'] += 1

    strengths = {}
    for k, s in stats.items():
        strengths[k] = {
            'attackHome':  (s['hg']/s['wh']/avg_h) if s['wh'] else 1.0,
            'defenseHome': (s['ha']/s['wh']/avg_a) if s['wh'] else 1.0,
            'attackAway':  (s['ag']/s['wa']/avg_a) if s['wa'] else 1.0,
            'defenseAway': (s['aa']/s['wa']/avg_h) if s['wa'] else 1.0,
            'n': s['n'],
        }
    return strengths, avg_h, avg_a

def compute_elo(matches):
    K = 20; ADV = 65
    elo = {}
    def get(k):
        if k not in elo: elo[k] = 1500
        return elo[k]
    for m in sorted(matches, key=lambda x: x['date']):
        k1, k2 = team_key(m['team1']), team_key(m['team2'])
        rh, ra = get(k1), get(k2)
        exp_elo = 1 / (1 + 10 ** (-((rh + ADV) - ra) / 400))
        actual = 1 if m['h'] > m['a'] else (0.5 if m['h'] == m['a'] else 0)
        exp_h = exp_elo
        o = m.get('odds') or {}
        if o.get('h') and o.get('d') and o.get('a'):
            try:
                inv = [1/o['h'], 1/o['d'], 1/o['a']]
                margin = sum(inv)
                market = (inv[0] + 0.5 * inv[1]) / margin
                exp_h = 0.5 * exp_elo + 0.5 * market
            except Exception:
                pass
        gd = abs(m['h'] - m['a'])
        gm = 1 if gd <= 1 else (1.5 if gd == 2 else 1.5 + (gd - 2) / 8)
        delta = K * gm * (actual - exp_h)
        elo[k1] = rh + delta
        elo[k2] = ra - delta
    return elo

# ---------------------------------------------------------------------------
# Sources de données
# ---------------------------------------------------------------------------
def fetch_fd_csv(fd_code, season_start):
    ssnn = f"{str(season_start)[-2:]}{str(season_start+1)[-2:]}"
    url = f"https://www.football-data.co.uk/mmz4281/{ssnn}/{fd_code}.csv"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        lines = [l for l in r.text.strip().split('\n') if l.strip()]
        headers = [h.strip() for h in lines[0].split(',')]
        rows = []
        for line in lines[1:]:
            cols = line.split(',')
            row = {headers[i]: cols[i].strip() if i < len(cols) else '' for i in range(len(headers))}
            if not row.get('HomeTeam') or not row.get('FTHG'): continue
            try:
                d, m, y = row['Date'].split('/')
                year = f"20{y}" if len(y) == 2 else y
                oh = float(row.get('PSCH') or row.get('B365H') or 0) or None
                od = float(row.get('PSCD') or row.get('B365D') or 0) or None
                oa = float(row.get('PSCA') or row.get('B365A') or 0) or None
                rows.append({
                    'date': f"{year}-{m.zfill(2)}-{d.zfill(2)}",
                    'team1': row['HomeTeam'], 'team2': row['AwayTeam'],
                    'h': int(row['FTHG']), 'a': int(row['FTAG']),
                    'odds': {'h': oh, 'd': od, 'a': oa} if oh and od and oa else None,
                })
            except Exception:
                continue
        print(f"  FD.co.uk {fd_code} {season_start}: {len(rows)} matchs")
        return rows
    except Exception as e:
        print(f"  FD.co.uk erreur {fd_code} {season_start}: {e}")
        return []

def fetch_club_elo():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    try:
        r = requests.get(f"https://api.clubelo.com/{today}", timeout=30)
        r.raise_for_status()
        lines = r.text.strip().split('\n')
        headers = [h.strip() for h in lines[0].split(',')]
        elos = {}
        for line in lines[1:]:
            cols = line.split(',')
            row = {headers[i]: cols[i].strip() if i < len(cols) else '' for i in range(len(headers))}
            if row.get('Club') and row.get('Elo'):
                try:
                    k = team_key(row['Club'])
                    val = float(row['Elo'])
                    if k not in elos or val > elos[k]:
                        elos[k] = val
                except Exception:
                    pass
        print(f"  ClubElo: {len(elos)} clubs")
        return elos
    except Exception as e:
        print(f"  ClubElo erreur: {e}")
        return {}

def fetch_espn_fixtures(league_code, days_ahead=14):
    start = datetime.utcnow()
    end   = start + timedelta(days=days_ahead)
    dr    = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    url   = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/"
             f"{league_code}/scoreboard?dates={dr}&limit=100")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        fixtures = []
        for ev in data.get('events', []):
            if ev.get('status', {}).get('type', {}).get('completed'):
                continue
            c = ev['competitions'][0]
            home = next((t for t in c['competitors'] if t['homeAway'] == 'home'), c['competitors'][0])
            away = next((t for t in c['competitors'] if t['homeAway'] == 'away'), c['competitors'][1])
            fixtures.append({
                'date': ev['date'],
                'home': {'name': home['team']['displayName'],
                         'shortName': home['team'].get('shortDisplayName', ''),
                         'logo': home['team'].get('logo', '')},
                'away': {'name': away['team']['displayName'],
                         'shortName': away['team'].get('shortDisplayName', ''),
                         'logo': away['team'].get('logo', '')},
            })
        print(f"  ESPN fixtures: {len(fixtures)}")
        return fixtures
    except Exception as e:
        print(f"  ESPN fixtures erreur: {e}")
        return []

def fetch_af_prediction(fixture_id):
    if not AF_KEY:
        return None
    try:
        r = requests.get(
            f"https://v3.football.api-sports.io/predictions?fixture={fixture_id}",
            headers={'x-apisports-key': AF_KEY}, timeout=20)
        r.raise_for_status()
        p = r.json().get('response', [{}])[0].get('predictions', {})
        pct = lambda s: (float(str(s).replace('%', '')) / 100) if s else None
        return {
            'home': pct(p.get('percent', {}).get('home')),
            'draw': pct(p.get('percent', {}).get('draw')),
            'away': pct(p.get('percent', {}).get('away')),
            'advice': p.get('advice'),
        }
    except Exception:
        return None

def fetch_espn_standings(league_code):
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_code}/standings"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        entries = []
        if data.get('children'):
            for g in data['children']:
                if g.get('standings', {}).get('entries'):
                    entries.extend(g['standings']['entries'])
        elif data.get('standings', {}).get('entries'):
            entries = data['standings']['entries']

        def stat(e, names):
            for n in names:
                s = next((x for x in e.get('stats', []) if x.get('name') == n or x.get('type') == n), None)
                if s: return s.get('displayValue') or s.get('value')
            return '–'

        return [{
            'rank': i + 1,
            'team': e['team'].get('shortDisplayName') or e['team'].get('displayName', ''),
            'logo': (e['team'].get('logos') or [{}])[0].get('href', ''),
            'gp':   stat(e, ['gamesPlayed']),
            'w':    stat(e, ['wins']),
            'd':    stat(e, ['ties', 'draws']),
            'l':    stat(e, ['losses']),
            'gd':   stat(e, ['pointDifferential', 'goalDifferential']),
            'pts':  stat(e, ['points']),
        } for i, e in enumerate(entries)]
    except Exception as e:
        print(f"  Standings erreur {league_code}: {e}")
        return []

# ---------------------------------------------------------------------------
# Génération des pronostics
# ---------------------------------------------------------------------------
def generate_league(league_code, cfg):
    print(f"\n=== {cfg['name']} ===")

    now = datetime.utcnow()
    current_season = now.year if now.month >= 7 else now.year - 1
    seasons = [current_season - 2, current_season - 1, current_season]

    all_matches = []
    for s in seasons:
        all_matches.extend(fetch_fd_csv(cfg['fdCode'], s))

    if not all_matches:
        print("  Aucune donnée historique — saut")
        return []

    club_elo = fetch_club_elo()
    strengths, avg_h, avg_a = compute_strengths(all_matches)
    elos = compute_elo(all_matches)
    fixtures = fetch_espn_fixtures(league_code)

    result = []
    for fix in fixtures:
        kh = team_key(fix['home']['name'])
        ka = team_key(fix['away']['name'])
        sh = strengths.get(kh)
        sa = strengths.get(ka)

        pred = {'date': fix['date'], 'home': fix['home'], 'away': fix['away'], 'hasModel': False}

        if sh and sa:
            lh = sh['attackHome'] * sa['defenseAway'] * avg_h
            la = sa['attackAway'] * sh['defenseHome'] * avg_a
            dc = dc_match(lh, la)
            ep = elo_probs(elos.get(kh, 1500), elos.get(ka, 1500))

            # ClubElo — essai avec la clé normalisée
            ce_h = club_elo.get(kh) or next((v for k, v in club_elo.items() if team_key(k) == kh), None)
            ce_a = club_elo.get(ka) or next((v for k, v in club_elo.items() if team_key(k) == ka), None)
            ce_p = elo_probs(ce_h, ce_a) if (ce_h and ce_a) else None

            externals = [ce_p]
            w_dc  = 0.40 if ce_p else 0.65
            w_elo = 0.25 if ce_p else 0.35
            w_ce  = 0.35 if ce_p else 0.0
            signals = [
                {**dc,  'weight': w_dc},
                {**ep,  'weight': w_elo},
            ]
            if ce_p: signals.append({**ce_p, 'weight': w_ce})

            tw = sum(s['weight'] for s in signals)
            ens_h = sum(s['home'] * s['weight'] for s in signals) / tw
            ens_d = sum(s['draw'] * s['weight'] for s in signals) / tw
            ens_a = sum(s['away'] * s['weight'] for s in signals) / tw
            total = ens_h + ens_d + ens_a

            mkt = derived(lh, la)
            sample = min(sh['n'], sa['n'])
            fav = max(ens_h, ens_d, ens_a) / total

            if   sample < 20 or fav < 0.43: conf = 'low';  label = 'Ouvert'
            elif fav > 0.60 and sample >= 40: conf = 'high'; label = 'Sûr'
            elif fav > 0.50:                  conf = 'high'; label = 'Probable'
            else:                             conf = 'med';  label = 'Serré'

            pred.update({
                'hasModel':   True,
                'pHome': round(ens_h / total * 100),
                'pDraw': round(ens_d / total * 100),
                'pAway': 100 - round(ens_h/total*100) - round(ens_d/total*100),
                'score': dc['score'],
                'lh': round(lh, 3), 'la': round(la, 3),
                'eloHome': round(elos.get(kh, 1500)),
                'eloAway': round(elos.get(ka, 1500)),
                'ceHome': round(ce_h) if ce_h else None,
                'ceAway': round(ce_a) if ce_a else None,
                'ou25': round(mkt['ou25'] * 100),
                'btts': round(mkt['btts'] * 100),
                'htScore': mkt['htScore'],
                'dc':  {'home': round(dc['home']*100), 'draw': round(dc['draw']*100), 'away': round(dc['away']*100)},
                'elo': {'home': round(ep['home']*100), 'draw': round(ep['draw']*100), 'away': round(ep['away']*100)},
                'ce':  {'home': round(ce_p['home']*100), 'draw': round(ce_p['draw']*100), 'away': round(ce_p['away']*100)} if ce_p else None,
                'sample': sample,
                'conf': conf, 'confLabel': label,
            })

        result.append(pred)

    return result

# ---------------------------------------------------------------------------
def main():
    print(f"Génération des pronostics — {datetime.utcnow().isoformat()}Z")
    print(f"API-Football : {'configurée' if AF_KEY else 'non configurée (GitHub Secret manquant)'}")

    output = {
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        'predictions': {},
        'standings': {},
    }

    for code, cfg in LEAGUES.items():
        output['predictions'][code] = generate_league(code, cfg)
        output['standings'][code]   = fetch_espn_standings(code)

    Path('data').mkdir(exist_ok=True)
    with open('data/predictions.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    total = sum(len(v) for v in output['predictions'].values())
    print(f"\n✅  data/predictions.json — {total} pronostics générés")

if __name__ == '__main__':
    main()
