require "yaml"
require "date"

path = ARGV[0]
doc = YAML.load_file(path)
errors = []

# 1. Every $ref points to an existing component
def walk(node, trail, &blk)
  case node
  when Hash
    node.each { |k, v| yield(k, v, trail); walk(v, trail + [k], &blk) }
  when Array
    node.each_with_index { |v, i| walk(v, trail + [i], &blk) }
  end
end

refs = []
walk(doc, []) { |k, v, t| refs << [v, t] if k == "$ref" }
refs.each do |ref, trail|
  unless ref.start_with?("#/")
    errors << "external ref #{ref}"
    next
  end
  target = ref.sub("#/", "").split("/").reduce(doc) { |n, p| n.is_a?(Hash) ? n[p] : nil }
  errors << "broken $ref #{ref} at #{trail.join('/')}" if target.nil?
end

# 2. Unquoted dates/times parsed by YAML (would not be JSON strings)
walk(doc, []) do |k, v, t|
  if v.is_a?(Date) || v.is_a?(Time)
    errors << "unquoted date at #{(t + [k]).join('/')}"
  end
end

# 3. Operations: summary, description, x-role, operationId unique, path params declared
ops = 0
ids = {}
methods = %w[get post put patch delete]
doc["paths"].each do |p, item|
  path_params = p.scan(/\{(\w+)\}/).flatten
  common = (item["parameters"] || [])
  methods.each do |m|
    op = item[m] or next
    ops += 1
    %w[summary description x-role operationId responses].each do |f|
      errors << "#{m.upcase} #{p} missing #{f}" unless op[f]
    end
    id = op["operationId"]
    errors << "duplicate operationId #{id}" if ids[id]
    ids[id] = true
    params = (common + (op["parameters"] || [])).map do |prm|
      prm = prm["$ref"].sub("#/", "").split("/").reduce(doc) { |n, x| n[x] } if prm["$ref"]
      prm
    end
    declared = params.select { |x| x["in"] == "path" }.map { |x| x["name"] }
    (path_params - declared).each { |pp| errors << "#{m.upcase} #{p} path param #{pp} not declared" }
    (declared - path_params).each { |pp| errors << "#{m.upcase} #{p} declares unknown path param #{pp}" }
    role = op["x-role"]
    errors << "#{m.upcase} #{p} role mismatch" if (p.start_with?("/backoffice") && role != "admin") ||
                                                 (p.start_with?("/appios") && role != "user") ||
                                                 (p.start_with?("/auth") && role != "public")
    if role != "public"
      %w[401 403].each { |c| errors << "#{m.upcase} #{p} missing #{c}" unless op["responses"][c] }
    end
    errors << "#{m.upcase} #{p} has 404 without path id or body" if false
  end
end

# 4. Unused components
used = refs.map(&:first).uniq
%w[schemas parameters responses].each do |sec|
  (doc["components"][sec] || {}).each_key do |name|
    errors << "unused component #{sec}/#{name}" unless used.include?("#/components/#{sec}/#{name}")
  end
end


# 5. No unexpected null and no stray keys (K1): nulls are allowed only inside examples
def walk_nulls(node, trail, errors)
  case node
  when Hash
    node.each do |k, v|
      next if %w[example examples].include?(k.to_s)
      errors << "null value at #{(trail + [k]).join('/')}" if v.nil?
      walk_nulls(v, trail + [k], errors)
    end
  when Array
    node.each_with_index { |v, i| walk_nulls(v, trail + [i], errors) unless v.nil? && trail.last.to_s == "enum" }
  end
end
walk_nulls(doc, [], errors)

SCHEMA_KEYS = %w[$ref type format description enum const default example examples items properties required
  minimum maximum exclusiveMinimum exclusiveMaximum minLength maxLength pattern minItems maxItems uniqueItems
  minProperties maxProperties allOf oneOf anyOf not if then else readOnly writeOnly additionalProperties
  nullable title deprecated]
def check_schema(s, trail, errors)
  return unless s.is_a?(Hash)
  s.each_key { |k| errors << "unknown schema keyword '#{k}' at #{trail.join('/')}" unless SCHEMA_KEYS.include?(k.to_s) }
  (s["properties"] || {}).each { |name, sub| check_schema(sub, trail + ["properties", name], errors) }
  check_schema(s["items"], trail + ["items"], errors) if s["items"].is_a?(Hash)
  %w[allOf oneOf anyOf].each { |kw| (s[kw] || []).each_with_index { |sub, i| check_schema(sub, trail + [kw, i], errors) } }
  %w[not if then else additionalProperties].each { |kw| check_schema(s[kw], trail + [kw], errors) if s[kw].is_a?(Hash) }
end
doc["components"]["schemas"].each { |name, sc| check_schema(sc, ["components", "schemas", name], errors) }
walk(doc, []) { |k, v, t| check_schema(v, t + [k], errors) if k == "schema" }

puts "paths=#{doc['paths'].size} operations=#{ops} refs=#{refs.size} schemas=#{doc['components']['schemas'].size}"
if errors.empty?
  puts "OK"
else
  puts errors
  exit 1
end
