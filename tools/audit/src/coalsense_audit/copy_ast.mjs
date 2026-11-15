// Parse only; never import or execute the audited source.
import ts from "typescript";
import { readFileSync } from "node:fs";
import process from "node:process";

const input = JSON.parse(readFileSync(0, "utf8"));
const findings = [];
const catalog = [];
const attributes = new Set(["aria-label", "title", "placeholder", "alt"]);

function unwrap(node) {
  while (
    node &&
    (ts.isParenthesizedExpression(node) ||
      ts.isAsExpression(node) ||
      ts.isSatisfiesExpression(node))
  )
    node = node.expression;
  return node;
}

function literal(node) {
  node = unwrap(node);
  return node && (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node));
}

// Whitespace/punctuation entities are not copy; any other entity or letter is.
const entities =
  /&(?:nbsp|ensp|emsp|thinsp|middot|bull|hellip|mdash|ndash|times|laquo|raquo|amp|lt|gt|quot|apos);/g;
const hasLetters = (text) => /\p{L}/u.test(text.replace(entities, ""));

// True when an expression can render a fixed string with letters (also through
// template literals with substitutions, ?:, &&, ||, ?? and +).
function visible(node) {
  node = unwrap(node);
  if (!node) return false;
  if (literal(node)) return hasLetters(node.text);
  if (ts.isTemplateExpression(node))
    return hasLetters(node.head.text) || node.templateSpans.some((s) => hasLetters(s.literal.text));
  if (ts.isConditionalExpression(node)) return visible(node.whenTrue) || visible(node.whenFalse);
  if (ts.isBinaryExpression(node)) return visible(node.left) || visible(node.right);
  return false;
}

for (const file of input) {
  const source = ts.createSourceFile(
    file.path,
    file.source,
    ts.ScriptTarget.Latest,
    true,
    file.catalog ? ts.ScriptKind.TS : ts.ScriptKind.TSX,
  );
  const line = (node) => source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
  const report = (node, rule) => findings.push(`${file.path}:${line(node)}: ${rule}`);
  if (source.parseDiagnostics.length) {
    findings.push(`${file.path}:1: ENTRADA: TypeScript inválido.`);
    continue;
  }
  if (file.catalog) {
    let found = false;
    function visit(node) {
      if (ts.isVariableDeclaration(node) && node.name.getText(source) === "es") {
        found = true;
        const object = unwrap(node.initializer);
        if (!object || !ts.isObjectLiteralExpression(object)) {
          report(node, "ENTRADA: Se esperaba un catálogo literal.");
          return;
        }
        for (const prop of object.properties) {
          if (
            !ts.isPropertyAssignment(prop) ||
            !ts.isStringLiteral(prop.name) ||
            !literal(prop.initializer)
          ) {
            report(prop, "ENTRADA: Se esperaban claves y valores de texto literales.");
            continue;
          }
          catalog.push({
            key: prop.name.text,
            value: unwrap(prop.initializer).text,
            line: line(prop),
          });
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
    if (!found) findings.push(`${file.path}:1: ENTRADA: Falta el catálogo es.`);
    continue;
  }
  function visit(node) {
    if (ts.isJsxText(node) && hasLetters(node.text)) {
      report(node, "CADENA_VISIBLE: Usar el catálogo es.");
    }
    if (
      ts.isJsxExpression(node) &&
      (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent)) &&
      visible(node.expression)
    ) {
      report(node, "CADENA_VISIBLE: Usar el catálogo es.");
    }
    if (ts.isJsxAttribute(node) && attributes.has(node.name.getText(source))) {
      const value = node.initializer;
      if (value && (literal(value) || (ts.isJsxExpression(value) && visible(value.expression)))) {
        report(node, "CADENA_VISIBLE: Usar el catálogo es para el atributo.");
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
}
process.stdout.write(JSON.stringify({ findings, catalog }));
