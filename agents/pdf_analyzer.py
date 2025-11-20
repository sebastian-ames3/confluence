"""
PDF Analyzer Agent

Extracts structured insights from PDF research reports.
Handles both text extraction and table parsing for macro research PDFs.

Priority Sources:
- 42 Macro: Around The Horn, Macro Scouting Report, KISS Model
- Discord: Options Insight weekly reports and market summaries
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import PyPDF2
import fitz  # PyMuPDF

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Lazy import for pdfplumber (to avoid cryptography DLL issues on Windows)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"pdfplumber not available: {e}. Will use PyPDF2 only.")
    PDFPLUMBER_AVAILABLE = False


class PDFAnalyzerAgent(BaseAgent):
    """
    Agent for extracting and analyzing PDF research reports.

    Pipeline:
    1. Extract text from PDF
    2. Extract tables (if any)
    3. Analyze with Claude to extract structured insights
    """

    # 42 Macro specific report types
    MACRO42_REPORT_TYPES = {
        "around the horn": "ath",
        "macro scouting report": "msr",
        "leadoff morning note": "leadoff",
        "kiss": "kiss_model"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize PDF Analyzer Agent.

        Args:
            api_key: Claude API key (defaults to env var)
            model: Claude model to use
        """
        super().__init__(api_key=api_key, model=model)
        logger.info(f"Initialized PDFAnalyzerAgent")

    def analyze(
        self,
        pdf_path: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Full pipeline: PDF → text+tables → analysis.

        Args:
            pdf_path: Path to PDF file
            source: Source of PDF (42macro, discord, etc.)
            metadata: Optional metadata (report_type, date, etc.)

        Returns:
            Complete analysis with extracted insights
        """
        if metadata is None:
            metadata = {}

        try:
            logger.info(f"Analyzing PDF: {pdf_path}")
            logger.info(f"Source: {source}")

            # Step 1: Extract text
            extracted_text = self.extract_text(pdf_path)

            # Step 2: Extract tables
            tables = self.extract_tables(pdf_path)

            # Step 3: Detect report type (for 42macro)
            report_type = self._detect_report_type(extracted_text, source, metadata)

            # Step 4: Analyze with Claude
            analysis = self.analyze_content(
                text=extracted_text,
                tables=tables,
                source=source,
                report_type=report_type,
                metadata=metadata
            )

            # Add metadata
            analysis["pdf_path"] = pdf_path
            analysis["source"] = source
            analysis["report_type"] = report_type
            analysis["page_count"] = self._get_page_count(pdf_path)
            analysis["processed_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"Analysis complete. Extracted {len(analysis.get('key_themes', []))} themes, "
                f"{len(tables)} tables"
            )

            return analysis

        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            raise

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract all text from PDF.

        Uses pdfplumber as primary method (better for modern PDFs).
        Falls back to PyPDF2 if pdfplumber fails or is not available.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text as string
        """
        logger.info(f"Extracting text from: {pdf_path}")

        # Try pdfplumber first if available
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text_parts = []
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")

                    extracted_text = "\n\n".join(text_parts)

                if extracted_text.strip():
                    logger.info(f"Extracted {len(extracted_text)} characters using pdfplumber")
                    return extracted_text
                else:
                    logger.warning("pdfplumber returned empty text, trying PyPDF2...")

            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}, falling back to PyPDF2...")

        # Fallback to PyPDF2
        return self._extract_text_pypdf2(pdf_path)

    def _extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        Fallback text extraction using PyPDF2.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

                return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PyPDF2 extraction also failed: {e}")
            raise Exception(f"All PDF extraction methods failed: {e}")

    def extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF.

        Uses pdfplumber to detect and extract tables.
        Returns empty list if pdfplumber is not available.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of extracted tables with metadata
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available, skipping table extraction")
            return []

        try:
            logger.info(f"Extracting tables from: {pdf_path}")

            tables_extracted = []

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables from page
                    page_tables = page.extract_tables()

                    for table_num, table in enumerate(page_tables, 1):
                        if table and len(table) > 0:
                            # Convert table to dict format
                            # First row is usually headers
                            headers = table[0] if table[0] else [f"col_{i}" for i in range(len(table[0]))]
                            rows = table[1:] if len(table) > 1 else []

                            table_dict = {
                                "page": page_num,
                                "table_number": table_num,
                                "headers": headers,
                                "rows": rows,
                                "row_count": len(rows),
                                "column_count": len(headers)
                            }

                            tables_extracted.append(table_dict)
                            logger.debug(
                                f"Extracted table {table_num} from page {page_num}: "
                                f"{len(rows)} rows, {len(headers)} columns"
                            )

            logger.info(f"Extracted {len(tables_extracted)} tables from PDF")
            return tables_extracted

        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
            return []

    def extract_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all images from PDF using PyMuPDF.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save extracted images (defaults to temp dir)

        Returns:
            List of extracted image metadata
        """
        try:
            logger.info(f"Extracting images from: {pdf_path}")

            # Create output directory if not specified
            if output_dir is None:
                pdf_name = Path(pdf_path).stem
                output_dir = os.path.join("temp", "extracted_images", pdf_name)

            os.makedirs(output_dir, exist_ok=True)

            extracted_images = []

            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Get list of images on this page
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list):
                    # Extract image data
                    xref = img[0]  # XREF number

                    # Get image metadata
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]  # png, jpeg, etc.

                    # Generate filename
                    image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)

                    # Save image to file
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    # Store metadata
                    image_metadata = {
                        "image_path": image_path,
                        "page_number": page_num + 1,
                        "image_index": img_index + 1,
                        "format": image_ext,
                        "size_bytes": len(image_bytes),
                        "xref": xref
                    }

                    extracted_images.append(image_metadata)

                    logger.debug(
                        f"Extracted image {img_index + 1} from page {page_num + 1}: "
                        f"{image_filename} ({len(image_bytes)} bytes)"
                    )

            # Store page count before closing document
            total_pages = len(doc)
            doc.close()

            logger.info(
                f"Extracted {len(extracted_images)} images from PDF "
                f"({total_pages} pages) to {output_dir}"
            )

            return extracted_images

        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise

    def analyze_content(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        source: str,
        report_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze extracted PDF content with Claude.

        Args:
            text: Extracted text from PDF
            tables: Extracted tables
            source: Source of PDF
            report_type: Type of report (ath, msr, leadoff, etc.)
            metadata: Additional metadata

        Returns:
            Structured analysis
        """
        try:
            logger.info(f"Analyzing content from {source} ({report_type})")

            # Build system prompt based on source and report type
            system_prompt = self._get_system_prompt(source, report_type)

            # Build user prompt
            user_prompt = self._build_analysis_prompt(text, tables, source, report_type, metadata)

            # Call Claude
            analysis = self.call_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.0,
                expect_json=True
            )

            # Validate response
            required_fields = [
                "key_themes",
                "tickers_mentioned",
                "conviction"
            ]
            self.validate_response_schema(analysis, required_fields)

            # Add extracted text and tables to response
            analysis["extracted_text"] = text
            analysis["tables"] = tables

            logger.info(
                f"Analysis complete: {len(analysis.get('key_themes', []))} themes, "
                f"conviction {analysis.get('conviction', 0)}/10"
            )

            return analysis

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            raise

    def _get_system_prompt(self, source: str, report_type: str) -> str:
        """
        Get system prompt based on source and report type.

        Args:
            source: Source of PDF
            report_type: Type of report

        Returns:
            System prompt for Claude
        """
        if source == "42macro":
            if report_type in ["ath", "around_the_horn"]:
                return """You are analyzing a 42 Macro "Around The Horn" report.

This is a comprehensive macro research report covering multiple markets, sectors, and asset classes.
It contains the KISS Model portfolio positioning, regime analysis, and market commentary.

Focus on:
- Market regime assessment (growth/inflation quadrant)
- KISS Model portfolio positioning (equities, bonds, commodities, cash weights)
- Key macro themes and catalysts
- Specific sector/ticker recommendations
- Valuation metrics and positioning data

Be precise with numbers, dates, and specific recommendations."""

            elif report_type in ["msr", "macro_scouting_report"]:
                return """You are analyzing a 42 Macro "Macro Scouting Report".

This is a weekly macro research report with deep dives into specific themes or markets.

Focus on:
- Primary investment thesis
- Supporting macro data and evidence
- Positioning recommendations
- Time horizon and catalysts
- Falsification criteria

Extract quantitative metrics where available."""

            elif report_type == "leadoff":
                return """You are analyzing a 42 Macro "Leadoff Morning Note".

This is a daily market commentary with timely analysis of overnight developments.

Focus on:
- Overnight market moves and catalysts
- Updated macro views
- Short-term trading implications
- Key levels and indicators to watch

Be concise and focus on actionable insights."""

        elif source == "discord":
            return """You are analyzing an Options Insight research report from Discord.

These reports typically focus on volatility analysis, options positioning, and technical levels.

Focus on:
- Volatility metrics (IV, RV, skew, term structure)
- Options positioning and flow
- Key technical levels
- Trade ideas and structures
- Risk/reward analysis

Extract specific strikes, expirations, and Greeks where mentioned."""

        # Default generic prompt
        return """You are analyzing an investment research PDF report.

Extract key investment themes, tickers, sentiment, and actionable insights.
Be thorough and precise with quantitative data."""

    def _build_analysis_prompt(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        source: str,
        report_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build analysis prompt for Claude.

        Args:
            text: Extracted text
            tables: Extracted tables
            source: Source
            report_type: Report type
            metadata: Metadata

        Returns:
            User prompt
        """
        # Truncate text if too long (Claude has token limits)
        max_text_length = 50000  # ~12,500 tokens worth of text
        truncated_text = text[:max_text_length]
        if len(text) > max_text_length:
            truncated_text += "\n\n[... text truncated for length ...]"

        # Format tables for prompt
        tables_summary = ""
        if tables:
            tables_summary = f"\n\n**Tables Extracted**: {len(tables)} tables found\n"
            for i, table in enumerate(tables[:5], 1):  # Limit to first 5 tables
                tables_summary += f"\nTable {i} (Page {table['page']}): "
                tables_summary += f"{table['row_count']} rows, {table['column_count']} columns\n"
                tables_summary += f"Headers: {table['headers']}\n"
                # Include first 3 rows as sample
                for row in table['rows'][:3]:
                    tables_summary += f"  {row}\n"

        prompt = f"""Analyze this investment research PDF report.

**Source**: {source}
**Report Type**: {report_type}
**Date**: {metadata.get('date', 'Unknown')}

**Extracted Text**:
{truncated_text}

{tables_summary}

Extract the following information in JSON format:

{{
    "key_themes": ["list of main macro/market themes discussed"],
    "market_regime": "growth_acceleration|growth_deceleration|stagflation|disinflationary_growth|unknown",
    "positioning": {{
        "equities": "overweight|neutral|underweight|not_mentioned",
        "bonds": "overweight|neutral|underweight|not_mentioned",
        "commodities": "overweight|neutral|underweight|not_mentioned",
        "cash": "high|medium|low|not_mentioned"
    }},
    "tickers_mentioned": ["specific securities, indexes, or assets with context"],
    "sentiment": "bullish|bearish|neutral|mixed",
    "conviction": <0-10 integer>,
    "time_horizon": "1d|1w|1m|3m|6m|6m+",
    "catalysts": ["upcoming events that matter for this thesis"],
    "falsification_criteria": ["what would invalidate this view"],
    "valuations": {{
        "spx_pe": <number or null>,
        "implied_earnings_growth": <number or null>,
        "other_metrics": {{"metric_name": value}}
    }},
    "key_quotes": ["3-5 most important quotes from the report"],
    "tables_analysis": ["what the tables show - positioning, metrics, etc."]
}}

Instructions:
- Focus on ACTIONABLE insights
- Extract specific numbers, dates, and levels where mentioned
- For KISS Model reports: extract exact portfolio weights if in tables
- For conviction: rate 0-10 based on strength of evidence and clarity of recommendation
- For falsification_criteria: be specific (e.g., "If 10Y yield >4.5%", not "if rates rise")
- If multiple themes discussed, focus on the primary/strongest thesis

Return ONLY valid JSON, no markdown formatting."""

        return prompt

    def _detect_report_type(
        self,
        text: str,
        source: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Detect report type from text content.

        Args:
            text: Extracted text
            source: Source
            metadata: Metadata

        Returns:
            Report type identifier
        """
        # Check metadata first
        if "report_type" in metadata:
            return metadata["report_type"]

        # For 42macro, detect from text
        if source == "42macro":
            text_lower = text.lower()
            for keyword, report_type in self.MACRO42_REPORT_TYPES.items():
                if keyword in text_lower:
                    logger.info(f"Detected 42macro report type: {report_type}")
                    return report_type

        return "general"

    def _get_page_count(self, pdf_path: str) -> int:
        """
        Get number of pages in PDF.

        Args:
            pdf_path: Path to PDF

        Returns:
            Number of pages
        """
        # Try pdfplumber first if available
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages)
            except:
                pass

        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except:
            return 0
