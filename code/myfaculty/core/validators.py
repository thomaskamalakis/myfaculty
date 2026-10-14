from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pypdf import PdfReader


def validate_pdf_file(f):
    """
    Ensure an uploaded file is a genuine, parseable PDF: checks the file
    extension, the '%PDF-' magic header and that pypdf can actually read it.

    Used on FileFields whose content later gets merged into an export PDF
    (see export.utils.append_filefield) - a file that looks like a PDF but
    isn't (e.g. a renamed .docx) would otherwise only fail much later, when
    building the export, and take the whole export down with it.
    """
    name = getattr(f, 'name', '') or ''
    if not name.lower().endswith('.pdf'):
        raise ValidationError(_('Το αρχείο πρέπει να είναι σε μορφή PDF (.pdf).'))

    pos = f.tell()
    try:
        f.seek(0)
        if f.read(5) != b'%PDF-':
            raise ValidationError(_('Το αρχείο δεν είναι έγκυρο αρχείο PDF.'))

        f.seek(0)
        PdfReader(f)
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_('Το αρχείο δεν είναι έγκυρο αρχείο PDF.'))
    finally:
        f.seek(pos)
