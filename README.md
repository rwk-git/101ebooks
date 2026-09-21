# 101 e-books

This repository is a fork of https://github.com/marinahane/101ebooks rebased on the original work https://github.com/101books/101books.github.io

It was created to fix issues with the problem books, both the PDFs and the e-books. To avoid things like:

- New duplicate policy, unless a problem is duplicated in the same book, the duplicates are kept, different books are allowed to share the same problems, this is the case with the physical books as well
- [Reverted colors in e-book problem rendering solution totally inadequate](https://www.reddit.com/r/baduk/s/vwKD7JKSLU)
- [Missing characters in 玄玄棋經 title](https://101books.github.io/pdfs/xuanxuan-qijing.pdf)
- Truncated solutions showing only 14 first moves
- Missing problems, false positive duplicates, fix or remove nonsensical or impossible problems
- Adding back full board problems that were missing in the PDF versions
- Update viewport on e-book version so that edges of the board are shown even when problem doesn't have stones on 1-2nd lines
- Improve solution where black plays suboptimal moves (e.g., lives with less points, wastes ko threats, make the opponent strong at the oustside for no reason), all verified with Katago
- etc.

This is a manually curated set of fixes, it takes time to fix there books for what some might consider minor issues. I do this for myself, I like the improvements I make to these books. Feel free to clone. Download page might be setup once I am done.