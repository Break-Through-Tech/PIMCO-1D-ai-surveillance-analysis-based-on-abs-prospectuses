"""
this file will orchestrate the calls 
it will grab the html filings 
and for each one, it runs the full pipeline : extract paragraph text, extract and classify tables (data, toc, junk)
then save the clean text and the "likely data" table to data/processed and writes a summary log (per_file counts, errors) in a json format 
if a file fails, it logs the error and keeps going 
"""