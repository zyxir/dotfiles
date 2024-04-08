//! Utility for console printing.

use std::path::Path;

/// Convert `obj` to string, and wrap it between `left` and `right` when running
/// in a terminal.
fn wrap<T: std::fmt::Display>(left: &str, obj: T, right: &str) -> String {
    if std::env::var("TERM").is_ok() {
        format!("{}{}{}", left, obj, right)
    } else {
        format!("{}", obj)
    }
}

/// Something that is emphasizable via [`emph`].
pub trait Emphasizable {
    fn emphed(&self) -> String;
}

impl Emphasizable for &str {
    /// Emphasize a string by making it bold.
    fn emphed(&self) -> String {
        wrap("\u{001b}[36m", self, "\u{001b}[0m")
    }
}

impl Emphasizable for &Path {
    /// Emphasize a path by making it cyan.
    fn emphed(&self) -> String {
        wrap("\u{001b}[36m", self.display(), "\u{001b}[0m")
    }
}

/// Emphasize `obj` according to its type.
pub fn emph<T: Emphasizable>(obj: T) -> String {
    obj.emphed()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emph_str() {
        let text = "Здравствуйте means 你好 in Chinese.";
        let emphed = emph(text);
        assert!(emphed.contains(text));
    }

    #[test]
    fn test_emph_path() {
        let path_str = "/usr/bin/bash";
        let emphed = emph(Path::new(path_str));
        assert!(emphed.contains(path_str));
    }
}
