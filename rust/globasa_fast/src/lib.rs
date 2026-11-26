//! globasa_fast: optional Rust versions of GlobasaLexiTools' hot loops.
//!
//! Each routine mirrors a Python original that stays in the repo as the reference and the
//! fallback (fast_ext.py prints "(fallback: ...)" when this extension is not built). The
//! linguistic tables are built in Python and handed over once, so no rule is duplicated here.
use pyo3::prelude::*;

mod align;
mod gestalt;
mod mst;

#[pymodule]
fn globasa_fast(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<align::Aligner>()?;
    m.add_function(wrap_pyfunction!(gestalt::ratio, m)?)?;
    m.add_function(wrap_pyfunction!(gestalt::quick_ratio, m)?)?;
    m.add_function(wrap_pyfunction!(gestalt::real_quick_ratio, m)?)?;
    m.add_function(wrap_pyfunction!(gestalt::matching_blocks, m)?)?;
    m.add_function(wrap_pyfunction!(gestalt::best_matches, m)?)?;
    m.add_function(wrap_pyfunction!(mst::chuliu_edmonds_one_root, m)?)?;
    Ok(())
}
