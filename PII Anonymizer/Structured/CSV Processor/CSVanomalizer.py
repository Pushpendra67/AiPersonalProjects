from presidio_structured import StructuredEngine, JsonAnalysisBuilder, PandasAnalysisBuilder, StructuredAnalysis, CsvReader, JsonReader, JsonDataProcessor, PandasDataProcessor
sample_df = CsvReader().read("test_structured.csv")
tabular_analysis = PandasAnalysisBuilder().generate_analysis(sample_df)
pandas_engine = StructuredEngine(data_processor=PandasDataProcessor())
df_to_be_anonymized = sample_df.copy() # in-place anonymization
anonymized_df = pandas_engine.anonymize(df_to_be_anonymized, tabular_analysis, operators=None) 

anonymized_df.to_csv("anonymized_test_structured.csv", index=False)

print(anonymized_df)