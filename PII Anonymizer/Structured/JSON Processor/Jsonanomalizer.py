import json
from presidio_structured import StructuredEngine, JsonAnalysisBuilder, PandasAnalysisBuilder, StructuredAnalysis, CsvReader, JsonReader, JsonDataProcessor, PandasDataProcessor
sample_json = JsonReader().read("test_struct.json")
sample_complex_json = JsonReader().read("test_structured_complex.json")

json_analysis = JsonAnalysisBuilder().generate_analysis(sample_json)




# # Currently does not support nested objects in lists
json_complex_analysis=""

try:
    json_complex_analysis = JsonAnalysisBuilder().generate_analysis(sample_complex_json)
except ValueError as e:
    print(e)

# # however, we can define it manually:
# json_complex_analysis = StructuredAnalysis(entity_mapping={
#     "users.name":"PERSON",
#     "users.address.street":"LOCATION",
#     "users.address.city":"LOCATION",
#     "users.address.state":"LOCATION",
#     "users.email": "EMAIL_ADDRESS",
# })



json_engine = StructuredEngine(data_processor=JsonDataProcessor())
anonymized_json = json_engine.anonymize(sample_json, json_analysis, operators=None)
with open("anonymized_sample.json", "w") as json_file:
    json.dump(anonymized_json, json_file, indent=4)
print(anonymized_json)


print("##################################################################################################################################")



#anonymized_complex_json = json_engine.anonymize(sample_complex_json, json_complex_analysis, operators=None)
# with open("anonymized_complex_sample.json", "w") as complex_json_file:
#     json.dump(anonymized_complex_json, complex_json_file, indent=4)

#print(anonymized_complex_json)