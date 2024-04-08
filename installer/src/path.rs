//! Utility for path manipulation.

use std::env;
use std::path::{Path, PathBuf};

// /// Normalize a path string into a Path object by:
// ///
// /// 1. Replace "~" with the user home directory.
// /// 2. Converting it to absolute path.
// pub fn path(path_str: &str) -> PathBuf {
//     let replaced = match env::var("HOME") {
//         Ok(home) => {
//             let replaced = path_str.replace("~", &home);
//             &PathBuf::from(replaced)
//         },
//         Err(_) => {
//             Path::new(path_str)
//         },
//     };
//     std::fs::canonicalize(replaced).unwrap()
// }

// #[cfg(test)]
// mod tests {
//     use super::*;

//     #[test]
//     fn test_path () {
//         println!("{}", path("~/.emacs.d/init.el").display())
//     }
// }
