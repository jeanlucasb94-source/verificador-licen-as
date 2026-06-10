"""
CLI — verificação rápida pelo terminal.

Exemplos:
  python cli.py FL --license CGC1234567
  python cli.py FL --name "SILVA CONSTRUCTION"
  python cli.py CA --license 123456
  python cli.py TX --license 12345        (mostra link oficial)
  python cli.py --states                  (lista estados suportados)
"""
import argparse
import json
import sys

import connectors


def main():
    p = argparse.ArgumentParser(description="Verificador de licenças profissionais (EUA)")
    p.add_argument("state", nargs="?", help="Sigla do estado (FL, CA, TX...)")
    p.add_argument("--license", "-l", help="Número da licença")
    p.add_argument("--name", "-n", help="Nome do profissional/empresa")
    p.add_argument("--json", action="store_true", help="Saída em JSON")
    p.add_argument("--states", action="store_true", help="Listar estados suportados")
    args = p.parse_args()

    if args.states or not args.state:
        print("Estados suportados:")
        for sigla, c in sorted(connectors.CONNECTORS.items()):
            kind = "automático" if sigla in ("FL", "CA") else "link oficial"
            print(f"  {sigla} — {c.state_name:<14} {c.agency}  [{kind}]")
        return

    conn = connectors.get(args.state)
    if not args.license and not args.name:
        p.error("informe --license ou --name")

    try:
        if args.license:
            results = conn.verify_by_number(args.license)
        else:
            results = conn.search_by_name(args.name)
    except NotImplementedError as e:
        print(f"[{conn.state}] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[{conn.state}] Erro: {e}")
        print(f"Verificação manual: {conn.manual_link(args.license or args.name or '')}")
        sys.exit(1)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
        return

    if not results:
        print(f"[{conn.state}] Nenhum registro encontrado.")
        print(f"Confirme no portal oficial: {conn.manual_link(args.license or args.name or '')}")
        return

    for r in results:
        valid = {True: "✅ VÁLIDA", False: "❌ NÃO VÁLIDA", None: "⚠️  CONFERIR"}[r.is_valid]
        print("-" * 60)
        print(f"{valid}  |  {r.state}  |  Licença: {r.license_number}")
        if r.holder_name:   print(f"  Titular:    {r.holder_name}")
        if r.license_type:  print(f"  Tipo:       {r.license_type}")
        if r.raw_status:    print(f"  Status:     {r.raw_status}")
        if r.expires:       print(f"  Expira em:  {r.expires}")
        if r.address:       print(f"  Endereço:   {r.address}")
        print(f"  Fonte:      {r.source}")
        note = r.extra.get("note")
        if note:            print(f"  Nota:       {note}")


if __name__ == "__main__":
    main()
