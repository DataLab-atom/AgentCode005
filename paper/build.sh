#!/bin/bash
# Build the Nature manuscript
# Usage: bash build.sh [main|supp|all|clean]

set -e

TARGET=${1:-all}

build_main() {
    echo "Building main manuscript..."
    pdflatex -interaction=nonstopmode main.tex
    bibtex main || true
    pdflatex -interaction=nonstopmode main.tex
    pdflatex -interaction=nonstopmode main.tex
    echo "Done: main.pdf"
}

build_supp() {
    echo "Building supplementary..."
    cd supplementary
    pdflatex -interaction=nonstopmode supplementary.tex
    pdflatex -interaction=nonstopmode supplementary.tex
    cd ..
    echo "Done: supplementary/supplementary.pdf"
}

clean() {
    echo "Cleaning auxiliary files..."
    rm -f *.aux *.bbl *.blg *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz
    rm -f supplementary/*.aux supplementary/*.log supplementary/*.out supplementary/*.toc
    echo "Done."
}

case $TARGET in
    main) build_main ;;
    supp) build_supp ;;
    all)  build_main; build_supp ;;
    clean) clean ;;
    *) echo "Usage: bash build.sh [main|supp|all|clean]" ;;
esac
