/* (d) The same scan + eight terms as a native routine, so the Python numbers
 * have a floor under them. Called through ctypes over the same packed columns
 * numpy holds, so the only difference from scoring_numpy.py is the language.
 *
 * Build:  make -C docs/research/bench/matcher-scale/native
 */
#include <math.h>
#include <stdint.h>

#define EARTH_R 6371.0088
#define STYLE_MASK 0x3Fu
#define VIBE_MASK 0x3FFC0u
#define CLASH_CAP 0.25

typedef struct {
    float mu, sigma, lat, lng, stale, tag_stale;
    uint32_t tags, grid, player_id;
    uint8_t sport, grid_bits, intent, ok;
} Row;

static double dr_tab[19];
static double prox_tab[21];
static int tabs_ready = 0;

static void init_tabs(void) {
    if (tabs_ready) return;
    for (int i = 0; i < 19; i++) dr_tab[i] = 1.0 - pow(0.45, (double)i);
    for (int i = 0; i < 21; i++) prox_tab[i] = exp(-((double)(i / 3)) / 5.0);
    tabs_ready = 1;
}

/* Returns the number of survivors written into out_fit / out_id. */
int32_t scan(const Row *rows, int32_t n,
             double mu0, double sigma0, double lat0, double lng0,
             double radius_km, uint32_t grid0, int32_t grid0_bits,
             uint32_t tags0, uint32_t comp_mask, uint32_t clash_mask,
             int32_t mode, uint8_t sport,
             double *out_fit, uint32_t *out_id) {
    init_tabs();
    const double w_lvl = mode == 0 ? 26.0 : 11.0;
    const double w_bal = mode == 0 ? 17.0 : 6.0;
    const double w_int = 14.0;
    const double w_avl = mode == 0 ? 11.0 : 16.0;
    const double w_sty = mode == 0 ? 9.0 : 11.0;
    const double w_vib = mode == 0 ? 4.0 : 22.0;
    const double w_dst = mode == 0 ? 6.0 : 11.0;
    const double intent_row[3][3] = {{1.0, 0.15, 0.6},
                                     {0.15, 1.0, 0.6},
                                     {0.6, 0.6, 1.0}};
    const double dlat = radius_km / 110.574;
    const double dlng = radius_km / (111.320 * cos(lat0 * M_PI / 180.0));
    const double lat_lo = lat0 - dlat, lat_hi = lat0 + dlat;
    const double lng_lo = lng0 - dlng, lng_hi = lng0 + dlng;
    const double lat0r = lat0 * M_PI / 180.0;
    const double cos_lat0 = cos(lat0r);
    const double sig0sq = sigma0 * sigma0;
    const double inv_mine = grid0_bits ? 1.0 / grid0_bits : 0.0;
    const double d_hi = 1.15 * radius_km, d_span = 1.0 / (0.45 * radius_km);
    const uint32_t ts = tags0 & STYLE_MASK, tv = tags0 & VIBE_MASK;
    const uint32_t cs = comp_mask & STYLE_MASK, cv = comp_mask & VIBE_MASK;
    const uint32_t ks = clash_mask & STYLE_MASK, kv = clash_mask & VIBE_MASK;

    int32_t k = 0;
    for (int32_t i = 0; i < n; i++) {
        const Row *c = &rows[i];
        if (c->sport != sport) continue;
        if (c->lat < lat_lo || c->lat > lat_hi) continue;
        if (c->lng < lng_lo || c->lng > lng_hi) continue;
        if (!c->ok) continue;

        const double clatr = c->lat * M_PI / 180.0;
        const double sla = sin((clatr - lat0r) * 0.5);
        const double slo = sin((c->lng - lng0) * M_PI / 360.0);
        const double km = 2.0 * EARTH_R *
            asin(sqrt(sla * sla + cos_lat0 * cos(clatr) * slo * slo));
        if (km > radius_km) continue;
        double v_dst = (d_hi - km) * d_span;
        if (v_dst > 1.0) v_dst = 1.0; else if (v_dst < 0.0) v_dst = 0.0;

        double acc = 0.0, wsum = 0.0;
        double d = c->mu - mu0; if (d < 0) d = -d;
        double v;
        if (mode == 0) { v = 1.0 - d / 0.55; }
        else { v = d > 0.25 ? 1.0 - (d - 0.25) / 0.65 : 1.0; }
        if (v < 0.0) v = 0.0;
        acc += w_lvl * v; wsum += w_lvl;

        double pct = 100.0 - d * 145.0 - sqrt(sig0sq + c->sigma * c->sigma) * 32.0;
        if (pct < 35.0) pct = 35.0; else if (pct > 96.0) pct = 96.0;
        acc += w_bal * ((pct - 35.0) / 61.0); wsum += w_bal;

        acc += w_int * intent_row[mode][c->intent]; wsum += w_int;

        uint32_t sh = grid0 & c->grid;
        if (sh && grid0_bits) {
            int n_sh = __builtin_popcount(sh);
            int theirs = c->grid_bits < grid0_bits ? c->grid_bits : grid0_bits;
            int slot = __builtin_ctz(sh);
            double av = (0.55 * (n_sh * inv_mine)
                         + 0.25 * ((double)n_sh / (theirs ? theirs : 1))
                         + 0.20 * prox_tab[slot > 20 ? 20 : slot]) * c->stale;
            acc += w_avl * av; wsum += w_avl;
        }

        uint32_t ct = c->tags;
        double st = dr_tab[__builtin_popcount(ts & ct)]
                  + 0.7 * dr_tab[__builtin_popcount(cs & ct)];
        double pen = __builtin_popcount(ks & ct) * 0.15;
        st -= pen > CLASH_CAP ? CLASH_CAP : pen;
        if (st > 1.0) st = 1.0; else if (st < 0.0) st = 0.0;
        acc += w_sty * st * c->tag_stale; wsum += w_sty;

        double vb = dr_tab[__builtin_popcount(tv & ct)]
                  + 0.7 * dr_tab[__builtin_popcount(cv & ct)];
        pen = __builtin_popcount(kv & ct) * 0.15;
        vb -= pen > CLASH_CAP ? CLASH_CAP : pen;
        if (vb > 1.0) vb = 1.0; else if (vb < 0.0) vb = 0.0;
        acc += w_vib * vb * c->tag_stale; wsum += w_vib;

        acc += w_dst * v_dst; wsum += w_dst;

        out_fit[k] = acc / wsum * 100.0;
        out_id[k] = c->player_id;
        k++;
    }
    return k;
}
