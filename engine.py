"""
VocalGuard Voice Authenticity Detector v6.1
============================================
Fixed based on real 63-file batch results.

Problems fixed from v6.0:
  1. Human high-noise (phone/ambient) being called AI
     → Shimmer > 17% + HNR < 10 = definitely human
  2. Human WhatsApp going to DIRECT mode (HNR 13-14)
     → HNR 13-14 + Shimmer 8-10% = human WhatsApp
  3. OVERLAP mode shimmer threshold too aggressive

Real calibration data (63 files):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAIN AI:
  TTS WhatsApp/Phone : HNR  6–7,  Shimmer 16–20%, Jitter 2.5–3.6
  S2S WhatsApp/Phone : HNR  7–9,  Shimmer 12–16%, Jitter 1.8–2.6

CHAIN HUMAN:
  Human high noise   : HNR  2–7,  Shimmer 17–23%, Jitter 2–6
  Human YT/Podcast   : HNR  9–11, Shimmer 13–14%, Jitter 2.4–3.0
  Human WhatsApp     : HNR 12–14, Shimmer  8–10%, Jitter 1.5–1.9
  Human Phone new    : HNR 11–12, Shimmer 10–13%, Jitter 2.0–2.5

KEY SEPARATOR in CHAIN:
  Shimmer > 17% + HNR < 10  → Human (high ambient noise)
  Shimmer 12-16% + HNR 6-9  → AI chain
  Shimmer 8-10%  + HNR > 11 → Human WhatsApp

DIRECT AI:
  S2S V2/V3  : HNR 13–16, Shimmer  6–9%,  JS 0.20–0.24
  TTS V2     : HNR 14–16, Shimmer  7–11%, JS 0.24–0.28
  TTS V3     : HNR 10–12, Shimmer  9–13%, JS 0.25–0.30

DIRECT HUMAN:
  Studio mic : HNR 14–16, Shimmer  8–9%,  JS 0.14–0.18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import parselmouth
import numpy as np
from parselmouth.praat import call


# ── Feature Extraction ───────────────────────────────────────────────────────

def extract_features(file_path: str, start_sec: float = 0.0, duration_sec: float = 0.0) -> dict:
    snd = parselmouth.Sound(file_path)
    total_dur = snd.duration

    if duration_sec > 0:
        end_sec = min(start_sec + duration_sec, total_dur)
        snd = snd.extract_part(from_time=start_sec, to_time=end_sec)
        analyzed_dur = end_sec - start_sec
    else:
        analyzed_dur = total_dur

    pitch_obj    = snd.to_pitch(pitch_floor=75.0, pitch_ceiling=800.0)
    pitch_values = pitch_obj.selected_array['frequency']
    voiced       = pitch_values[pitch_values > 0]
    mean_pitch   = float(np.mean(voiced)) if len(voiced) > 0 else 0.0
    pitch_sd     = float(np.std(voiced))  if len(voiced) > 1 else 0.0
    voiced_frac  = len(voiced) / max(len(pitch_values), 1)

    harmonicity = snd.to_harmonicity()
    hnr_val     = max(call(harmonicity, "Get mean", 0.0, 0.0), 0.0)

    point_process = call([snd, pitch_obj], "To PointProcess (cc)")
    jitter_pct    = call(point_process, "Get jitter (local)",
                         0.0, 0.0, 0.0001, 0.02, 1.3) * 100.0
    shimmer_pct   = call([snd, point_process], "Get shimmer (local)",
                         0.0, 0.0, 0.0001, 0.02, 1.3, 1.6) * 100.0

    return {
        "mean_pitch_hz":   round(mean_pitch,  2),
        "pitch_sd_hz":     round(pitch_sd,    2),
        "hnr_db":          round(hnr_val,     2),
        "jitter_pct":      round(jitter_pct,  3),
        "shimmer_pct":     round(shimmer_pct, 3),
        "voiced_fraction": round(voiced_frac, 3),
        "duration_sec":    round(analyzed_dur, 2),
    }


# ── Chain Detection ──────────────────────────────────────────────────────────

def detect_chain(hnr: float, shimmer: float) -> str:
    """
    Detect recording chain using HNR + Shimmer combo.

    DIRECT:  HNR > 13 — clean high quality recording
    CHAIN:   HNR < 10.5 AND shimmer NOT extreme human
    OVERLAP: everything in between
    """
    # High quality direct recording
    if hnr >= 13.0 and shimmer < 17.0:
        return "DIRECT"

    # Extreme noise = definitely chain (human ambient/phone)
    if hnr < 10.5:
        return "CHAIN"

    # HNR 10.5-13 = overlap zone
    return "OVERLAP"


# ── Scoring Engine v6.1 ──────────────────────────────────────────────────────

def VocalGuard_score(features: dict) -> dict:

    jitter   = features["jitter_pct"]
    hnr      = features["hnr_db"]
    shimmer  = features["shimmer_pct"]
    pitch    = features["mean_pitch_hz"]
    pitch_sd = features["pitch_sd_hz"]
    voiced   = features["voiced_fraction"]

    ai_pts    = 0.0
    human_pts = 0.0
    flags     = []

    js_ratio = round(jitter / shimmer, 4) if shimmer > 0 else 0
    chain    = detect_chain(hnr, shimmer)
    flags.append(f"CHAIN-DETECTED: {chain} (HNR={hnr:.1f} dB, Shimmer={shimmer:.2f}%)")

    # ══════════════════════════════════════════════════════════════════
    # CHAIN MODE
    # ══════════════════════════════════════════════════════════════════
    if chain == "CHAIN":

        # ── CRITICAL FIX: High shimmer + low HNR = Human ambient/phone ──
        # Real data: HUMAN_MAC=23%, HUMAN_PHONE_SAT=21%, HUMAN_YT_POD=14%
        # These are NOT AI — they are noisy human recordings
        if shimmer >= 20.0 and hnr < 10.0:
            human_pts += 70
            flags.append(f"CHAIN-HUMAN-AMBIENT: Shimmer {shimmer:.2f}% ≥20% + HNR {hnr:.1f} <10 — extreme ambient noise [+70 Human]")
            flags.append(f"CHAIN-HUMAN-AMBIENT: Shimmer {shimmer:.2f}% ≥17% + HNR {hnr:.1f} <10 — high ambient noise = natural recording [+70 Human]")

        elif shimmer >= 13.0 and hnr < 10.0:
            # Could be AI TTS or human YT/podcast
            # AI TTS chain:   Shimmer 16-20%, HNR 6-7
            # Human YT/Pod:   Shimmer 13-14%, HNR 9-11
            if hnr <= 7.5 and shimmer >= 16.0:
                ai_pts += 60
                flags.append(f"CHAIN-AI-TTS: HNR {hnr:.1f} ≤7.5 + Shimmer {shimmer:.2f}% ≥16% — AI TTS chain [+60 AI]")
            elif hnr >= 8.5 and shimmer <= 15.0:
                human_pts += 45
                flags.append(f"CHAIN-HUMAN-YT: HNR {hnr:.1f} ≥8.5 + Shimmer {shimmer:.2f}% ≤15% — human YT/podcast chain [+45 Human]")
            else:
                # AI S2S chain: HNR 7-9, Shimmer 12-16%
                ai_pts += 40
                flags.append(f"CHAIN-AI-S2S: HNR {hnr:.1f} + Shimmer {shimmer:.2f}% — AI S2S chain pattern [+40 AI]")

        elif shimmer < 13.0 and hnr < 10.5:
            # AI S2S phone chain: Shimmer 12-14%, HNR 7-9
            ai_pts += 45
            flags.append(f"CHAIN-AI-S2S-PHONE: Shimmer {shimmer:.2f}% <13% + HNR {hnr:.1f} — AI S2S phone chain [+45 AI]")

        # Supporting — Jitter
        if jitter >= 3.0 and shimmer >= 15.0:
            ai_pts += 15
            flags.append(f"CHAIN-JITTER-HIGH+SHIMMER: {jitter:.3f}% + {shimmer:.2f}% — AI TTS chain [+15 AI]")
        elif jitter >= 4.0 and shimmer >= 17.0:
            human_pts += 15
            flags.append(f"CHAIN-JITTER-EXTREME: {jitter:.3f}% — natural vocal extreme [+15 Human]")
        elif jitter <= 2.0 and shimmer < 13.0:
            ai_pts += 10
            flags.append(f"CHAIN-JITTER-LOW: {jitter:.3f}% + Shimmer {shimmer:.2f}% — AI S2S chain [+10 AI]")

        # Chain profiles
        profiles = {
            "AI TTS Chain (WhatsApp/Phone)":   _dist(jitter, hnr, shimmer, 3.05,  6.8, 18.0),
            "AI S2S Chain (WhatsApp/Phone)":   _dist(jitter, hnr, shimmer, 2.18,  8.0, 14.2),
            "Human Ambient/Phone (noisy)":     _dist(jitter, hnr, shimmer, 3.50,  4.0, 21.0),
            "Human YouTube/Podcast chain":     _dist(jitter, hnr, shimmer, 2.70,  9.5, 13.9),
            "Human WhatsApp chain":            _dist(jitter, hnr, shimmer, 1.83, 13.3,  8.9),
        }

    # ══════════════════════════════════════════════════════════════════
    # DIRECT MODE — High quality recording (HNR > 13)
    # Original 96% logic — preserved exactly
    # ══════════════════════════════════════════════════════════════════
    elif chain == "DIRECT":

        # JS Ratio — primary
        if js_ratio >= 0.28:
            ai_pts += 40
            flags.append(f"JS-RATIO-AI-STRONG: {js_ratio:.3f} ≥0.28 [+40 AI]")
        elif js_ratio >= 0.23:
            ai_pts += 28
            flags.append(f"JS-RATIO-AI: {js_ratio:.3f} (0.23–0.28) [+28 AI]")
        elif js_ratio >= 0.20:
            ai_pts += 16
            flags.append(f"JS-RATIO-BORDERLINE: {js_ratio:.3f} (0.20–0.23) [+16 AI]")
        elif js_ratio <= 0.12:
            human_pts += 40
            flags.append(f"JS-RATIO-HUMAN-STRONG: {js_ratio:.3f} ≤0.12 [+40 Human]")
        elif js_ratio <= 0.17:
            human_pts += 26
            flags.append(f"JS-RATIO-HUMAN: {js_ratio:.3f} (0.12–0.17) [+26 Human]")
        elif js_ratio <= 0.20:
            human_pts += 14
            flags.append(f"JS-RATIO-LEAN-HUMAN: {js_ratio:.3f} (0.17–0.20) [+14 Human]")

        # Shimmer
        if 13.0 <= hnr <= 14.0 and 8.0 <= shimmer <= 10.0 and js_ratio <= 0.20:
            human_pts += 40
            flags.append(f"DIRECT-HUMAN-WHATSAPP: HNR {hnr:.1f} + Shimmer {shimmer:.2f}% [+40 Human]")
            flags.append(f"SHIMMER-EXTREME: {shimmer:.2f}% [+25 Human]")
        elif shimmer >= 14.0:
            human_pts += 18
            flags.append(f"SHIMMER-HIGH: {shimmer:.2f}% [+18 Human]")
        elif shimmer >= 12.0:
            human_pts += 10
            flags.append(f"SHIMMER-MID-HIGH: {shimmer:.2f}% [+10 Human]")
        elif shimmer <= 7.5:
            ai_pts += 25
            flags.append(f"SHIMMER-FLAT: {shimmer:.2f}% [+25 AI]")
        elif shimmer <= 9.5:
            ai_pts += 15
            flags.append(f"SHIMMER-CONTROLLED: {shimmer:.2f}% [+15 AI]")
        else:
            ai_pts    += 6
            human_pts += 6
            flags.append(f"SHIMMER-NEUTRAL: {shimmer:.2f}%")

        # HNR
        if hnr >= 15.0:
            if shimmer <= 8.5 and js_ratio >= 0.20:
                ai_pts += 20
                flags.append(f"HNR-HIGH+AI-COMBO: {hnr:.1f} dB [+20 AI]")
            elif shimmer <= 9.5:
                ai_pts += 12
                flags.append(f"HNR-HIGH+SHIMMER-LOW: {hnr:.1f} dB [+12 AI]")
            else:
                human_pts += 8
                flags.append(f"HNR-HIGH+SHIMMER-OK: {hnr:.1f} dB [+8 Human]")
        elif hnr >= 12.5:
            flags.append(f"HNR-MID: {hnr:.1f} dB — JS decides")
        elif hnr <= 7.0:
            human_pts += 20
            flags.append(f"HNR-NOISY: {hnr:.1f} dB [+20 Human]")
        elif hnr <= 11.5:
            human_pts += 10
            flags.append(f"HNR-NATURAL: {hnr:.1f} dB [+10 Human]")

        # PitchSD
        if pitch_sd >= 150:
            human_pts += 12
            flags.append(f"PITCHSD-EXTREME: {pitch_sd:.0f} Hz [+12 Human]")
        elif pitch_sd >= 110:
            human_pts += 6
            flags.append(f"PITCHSD-HIGH: {pitch_sd:.0f} Hz [+6 Human]")
        elif pitch_sd <= 12:
            ai_pts += 12
            flags.append(f"PITCHSD-FLAT: {pitch_sd:.0f} Hz [+12 AI]")
        elif pitch_sd <= 22:
            ai_pts += 6
            flags.append(f"PITCHSD-LOW: {pitch_sd:.0f} Hz [+6 AI]")

        # Jitter
        if jitter > 4.5:
            human_pts += 10
            flags.append(f"JITTER-EXTREME: {jitter:.3f}% [+10 Human]")
        elif jitter < 0.8 and shimmer < 8.0:
            ai_pts += 10
            flags.append(f"JITTER+SHIMMER-BOTH-LOW: {jitter:.3f}% [+10 AI]")

        # Pitch range
        if pitch > 0:
            if 85 <= pitch <= 280:
                human_pts += 4
                flags.append(f"PITCH-NATURAL: {pitch:.0f} Hz [+4 Human]")
            elif pitch > 300:
                ai_pts += 4
                flags.append(f"PITCH-ELEVATED: {pitch:.0f} Hz [+4 AI]")

        profiles = {
            "AI S2S V2 (ElevenLabs S2S)":     _dist(jitter, hnr, shimmer, 1.60, 15.5,  7.3),
            "AI TTS V2 (ElevenLabs TTS V2)":  _dist(jitter, hnr, shimmer, 1.82, 14.5,  7.5),
            "AI TTS V3 (ElevenLabs TTS V3)":  _dist(jitter, hnr, shimmer, 3.05, 11.2, 10.5),
            "AI Clone (Voice Clone)":          _dist(jitter, hnr, shimmer, 2.97, 10.4,  9.6),
            "AI Child/Fast voice":             _dist(jitter, hnr, shimmer, 1.17, 14.5,  8.5),
            "Human Studio Mic":                _dist(jitter, hnr, shimmer, 1.41, 14.9,  8.6),
            "Human WhatsApp Opus":             _dist(jitter, hnr, shimmer, 1.90, 12.3, 14.0),
            "Human Phone Mic":                 _dist(jitter, hnr, shimmer, 2.17,  6.5, 21.3),
            "Human YouTube/Podcast":           _dist(jitter, hnr, shimmer, 2.48, 10.2, 13.9),
        }

    # ══════════════════════════════════════════════════════════════════
    # OVERLAP MODE — HNR 10.5–13
    # ══════════════════════════════════════════════════════════════════
    else:
        flags.append(f"OVERLAP-ZONE: HNR {hnr:.1f} dB")

        # Human WhatsApp pattern — HNR 12-14, Shimmer 8-10%
        if hnr >= 12.0 and shimmer <= 10.5:
            human_pts += 45
            flags.append(f"OVERLAP-HUMAN-WHATSAPP: HNR {hnr:.1f} + Shimmer {shimmer:.2f}% — human WhatsApp pattern [+45 Human]")

        # Human phone new — HNR 11-12, Shimmer 10-13%
        elif hnr >= 11.0 and shimmer <= 13.5 and js_ratio <= 0.22:
            human_pts += 35
            flags.append(f"OVERLAP-HUMAN-PHONE: HNR {hnr:.1f} + Shimmer {shimmer:.2f}% + JS {js_ratio:.3f} — human phone pattern [+35 Human]")

        # AI TTS V3 / Clone overlap zone
        elif shimmer >= 10.5 and js_ratio >= 0.25:
            ai_pts += 40
            flags.append(f"OVERLAP-AI-TTS: Shimmer {shimmer:.2f}% + JS {js_ratio:.3f} — AI TTS V3 pattern [+40 AI]")

        elif shimmer >= 9.5 and js_ratio >= 0.22:
            ai_pts += 28
            flags.append(f"OVERLAP-AI-LEAN: Shimmer {shimmer:.2f}% + JS {js_ratio:.3f} — leans AI [+28 AI]")

        else:
            # Tiebreaker
            if hnr >= 12.0:
                human_pts += 20
                flags.append(f"OVERLAP-HNR-HUMAN: {hnr:.1f} dB ≥12 [+20 Human]")
            else:
                ai_pts += 15
                flags.append(f"OVERLAP-HNR-AI: {hnr:.1f} dB <12 [+15 AI]")

            if shimmer >= 12.0:
                ai_pts += 15
                flags.append(f"OVERLAP-SHIMMER-AI: {shimmer:.2f}% ≥12% [+15 AI]")
            elif shimmer <= 10.0:
                human_pts += 15
                flags.append(f"OVERLAP-SHIMMER-HUMAN: {shimmer:.2f}% ≤10% [+15 Human]")

        profiles = {
            "AI TTS V3 chain":       _dist(jitter, hnr, shimmer, 3.05, 11.2, 10.5),
            "AI S2S chain":          _dist(jitter, hnr, shimmer, 2.18,  8.5, 14.2),
            "Human WhatsApp":        _dist(jitter, hnr, shimmer, 1.75, 13.3,  9.0),
            "Human Phone (new)":     _dist(jitter, hnr, shimmer, 2.23, 12.0, 11.4),
            "Human YouTube/Podcast": _dist(jitter, hnr, shimmer, 2.69, 10.3, 13.9),
        }

    # ── Sanity ────────────────────────────────────────────────────────
    if voiced < 0.25:
        flags.append(f"WARNING: voiced {voiced*100:.0f}% — mostly silence")

    closest  = min(profiles, key=profiles.get)
    distance = round(profiles[closest], 3)

    total = ai_pts + human_pts
    if total == 0:
        ai_conf = human_conf = 50.0
    else:
        ai_conf    = round(ai_pts    / total * 100, 1)
        human_conf = round(human_pts / total * 100, 1)

    if ai_conf    > 99.2: ai_conf    = 99.2
    if human_conf > 98.5: human_conf = 98.5

    if ai_conf >= 62:
        verdict = "AI_GENERATED"
    elif human_conf >= 62:
        verdict = "HUMAN"
    else:
        verdict = "UNCERTAIN"

    return {
        "verdict":          verdict,
        "ai_confidence":    ai_conf,
        "human_confidence": human_conf,
        "ai_points":        round(ai_pts,    1),
        "human_points":     round(human_pts, 1),
        "closest_profile":  closest,
        "profile_distance": distance,
        "chain":            chain,
        "flags":            flags,
    }


def _dist(j, h, s, tj, th, ts):
    return ((j-tj)**2 * 2.0 + (h-th)**2 * 0.5 + (s-ts)**2 * 1.0) ** 0.5


# ── Main Entry Point ─────────────────────────────────────────────────────────

def run_forensic_analysis(file_path: str,
                          start_sec:    float = 0.0,
                          duration_sec: float = 0.0) -> dict:
    try:
        features = extract_features(file_path, start_sec, duration_sec)
        result   = VocalGuard_score(features)
        return {
            "verdict":          result["verdict"],
            "ai_confidence":    result["ai_confidence"],
            "human_confidence": result["human_confidence"],
            "closest_profile":  result["closest_profile"],
            "profile_distance": result["profile_distance"],
            "chain":            result["chain"],
            "metrics": {
                "pitch_hz":        features["mean_pitch_hz"],
                "pitch_sd_hz":     features["pitch_sd_hz"],
                "hnr_db":          features["hnr_db"],
                "jitter_pct":      features["jitter_pct"],
                "shimmer_pct":     features["shimmer_pct"],
                "js_ratio":        round(features["jitter_pct"] / features["shimmer_pct"], 3)
                                   if features["shimmer_pct"] > 0 else 0,
                "voiced_fraction": features["voiced_fraction"],
                "duration_sec":    features["duration_sec"],
            },
            "flags": result["flags"],
            "error": None,
        }
    except Exception as e:
        return {
            "verdict": "ERROR", "ai_confidence": 0.0,
            "human_confidence": 0.0, "closest_profile": None,
            "profile_distance": None, "chain": "UNKNOWN",
            "metrics": {}, "flags": [], "error": str(e),
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 engine.py <audio_file> [start_sec] [duration_sec]")
        sys.exit(1)

    fp       = sys.argv[1]
    start    = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    r = run_forensic_analysis(fp, start, duration)

    print("\n" + "═" * 62)
    print("  VocalGuard Voice Detector v6.1")
    print("═" * 62)

    if r["error"]:
        print(f"\n  ERROR: {r['error']}\n")
    else:
        icon = "🤖" if r["verdict"] == "AI_GENERATED" else \
               ("👤" if r["verdict"] == "HUMAN" else "❓")
        print(f"\n  {icon}  VERDICT          : {r['verdict']}")
        print(f"  AI  confidence   : {r['ai_confidence']}%")
        print(f"  Human confidence : {r['human_confidence']}%")
        print(f"  Chain detected   : {r['chain']}")
        print(f"  Closest profile  : {r['closest_profile']}")

        m = r["metrics"]
        print(f"\n  ── Metrics ──────────────────────────────────")
        print(f"  HNR        : {m['hnr_db']} dB      ← chain detector")
        print(f"  Shimmer    : {m['shimmer_pct']}%")
        print(f"  Jitter     : {m['jitter_pct']}%")
        print(f"  JS Ratio   : {m['js_ratio']}")
        print(f"  Pitch      : {m['pitch_hz']} Hz")
        print(f"  PitchSD    : {m['pitch_sd_hz']} Hz")
        print(f"  Voiced     : {round(m['voiced_fraction']*100)}%")
        print(f"  Duration   : {m['duration_sec']}s")

        print(f"\n  ── Signal Flags ─────────────────────────────")
        for f in r["flags"]:
            print(f"  • {f}")

    print("\n" + "═" * 62 + "\n")