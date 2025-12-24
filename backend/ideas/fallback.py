def fallback_ideas(domain: str) -> list[str]:
    d = domain.lower()

    return [
        f"Stability guarantees for nonlinear {d} models under delayed and partially observed feedback",
        f"Identifiability limits in data-driven estimation of high-dimensional {d} systems",
        f"Robust control synthesis for stochastic {d} systems with structured model uncertainty",
        f"Bifurcation-aware learning of reduced-order representations in chaotic {d} dynamics",
        f"Provable convergence of adaptive controllers for non-stationary {d} environments"
    ]
