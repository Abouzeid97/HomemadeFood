import json

with open('initial_data_fixture.json', 'r') as f:
    fixture = json.load(f)

# Add updated_at to all chef and consumer entries that don't have it
fixed_count = 0
for item in fixture:
    if item['model'] in ['authentication.chef', 'authentication.consumer']:
        if 'updated_at' not in item['fields']:
            item['fields']['updated_at'] = item['fields']['created_at']
            print(f'Added updated_at to {item["model"]} pk={item["pk"]}')
            fixed_count += 1

with open('initial_data_fixture.json', 'w') as f:
    json.dump(fixture, f, indent=2)

print(f'Fixed {fixed_count} entries!')
