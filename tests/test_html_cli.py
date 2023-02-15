from h5glance.html_cli import main

def test_html_cli_write(tmp_path, closed_h5_file):
    out_file = tmp_path / 'out.html'
    main([str(closed_h5_file), '-w', str(out_file)])
    assert out_file.is_file()
