import os
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from main import get_session, app
from app.utils import get_password_hash
from app.models import Student
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import pytest

load_dotenv(".env")


authorization_token_for_create_student = os.getenv("TOKEN_FOR_CREATE_STUDENT")
test_access_token = os.getenv("TEST_ACCESS_TOKEN")
test_refresh_token = os.getenv("TEST_REFRESH_TOKEN")


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_student(client: TestClient):
    
    response = client.post(
        url="/create-student",
        headers={"Authorization": f"Bearer {authorization_token_for_create_student}"},
        json={"matric_number": "21cg029882", "password": "password"}
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json() == {
        "matric_number": "21CG029882", "password": "sike, you thought you were getting the original thing"}


def test_verify_student(session: Session, client: TestClient):
    student = Student(
        matric_number="21CG029883", password=get_password_hash("password"), device_registered=True)

    session.add(student)
    session.commit()

    response = client.post(
        "/verify-student",
        json={"matric_number": "21cg029883", "password": "password"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data and "token_type" in data and "refresh_token" in data


def test_verify_student_incomplete(client: TestClient):
    response = client.post(
        "/verify-student",
        # i removed the mandatory password field
        json={"matric_number": "21cg029882"}
    )

    assert response.status_code == 422


def test_verify_student_wrong_info(client: TestClient):
    # included a wrong password
    response = client.post(
        "/verify-student",
        json={"matric_number": "21cg029882", "password": "pasdsword"}
    )

    assert response.status_code == 401

def test_verify_student_unregistered_device(client: TestClient, session: Session):
    student = Student(
        matric_number="21CG029883", password=get_password_hash("password"))

    session.add(student)
    session.commit()

    response = client.post(
        "/verify-student",
        json={"matric_number": "21cg029883", "password": "password"}
    )

    assert response.status_code == 403

def test_generate_registration_options(session: Session, client: TestClient):
    student = Student(
        matric_number="21CG029882", password=get_password_hash("password"))

    # We need to create this student because the dependencies query the database to ensure the matric_number in the jwt is valid
    session.add(student)
    session.commit()

    response = client.get(
        url="/generate-registration-options?matric_number=21CG029882",
        headers={"Authorization": f"Bearer {authorization_token_for_create_student}"}
    )
    assert response.status_code == 200


# def test_verify_registration_options(session: Session, client: TestClient):
#     student = Student(
#         matric_number="21CG029882", password=get_password_hash("password"))

#     session.add(student)
#     session.commit()
#     import json
#     request = {"id": "J8LcFVvI4IoS2lhc11jKXS8HeYLzObZTtH6bQC589Uc", "rawId": "J8LcFVvI4IoS2lhc11jKXS8HeYLzObZTtH6bQC589Uc", "response": {"attestationObject": "o2NmbXRmcGFja2VkZ2F0dFN0bXSiY2FsZzkBAGNzaWdZAQAjWKkdvwekglPKanLJ1r1elbVyeH--FuBsqFN5jrSbxX6mpQps1U-EV8eupBwIUgak9tldQg564FSofeKs-HU88uYPycdFTB6R0zAwZ82f6jrDXSTFfuTJgcPDhZSneAaiG8DeHMCF0L9kHDDjhyLbpvQwKhwpXkYwOr_uXQx7d1FTT5Pi29-PEF0mqKiK5K2UbJpdCQ5K4mdm2RVUbcqvMFU4miwTZYAUFrf3HP-gbvOh0rGCeKZso1A5nHCurFAE6KLGiGy5u_57GbLFkPZRXG6n1-vQDQAkr23NX2U9M0FGho1QR3LDhVuYwo1Cba-oQXmBl_CU1HFWg-mB6kQtaGF1dGhEYXRhWQFnUqQfTrZcyyiUtScGG6dIfyg1it78fY-Ey_XPk07MeplFAAAAAGAosBex1EwCtLOvza_Ja7IAICfC3BVbyOCKEtpYXNdYyl0vB3mC8zm2U7R-m0AufPVHpAEDAzkBACBZAQDHfJukI12-OknPb7xisVM2gzILC1ekMLun7cZBMKiH0THVV6v2-ykR7r9wf2ldZW3CL_ps4ycVSBiGWeDzpUVP8OJssklTsOMdcqevrCnasirSYQN-H3wp3yhTVC6Hg3WsggsPNbeRnWDC1lYo7OZuNfz4g5GyB7uYhx6Wl9qQhscHXI6AOkyXHTYtfYyoLf1kMzJgXKEQZcUaR4QZWtT9abHqzFI_dca1qjYDW22Mji9nX3LjjeCF_C41kUYOpWDXBSY3Zf3GWdpIl0-teJrOram6yWb3KaYnqS0K5rqPlV3da8EafpIwXespe2RD4K7zNbC3a-qz4nUlL_fXgsuZIUMBAAE", "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoicFFhOFdfUVNQUEc3TzI3UGtpa3hSRDI4dW42NHdIRDdGQlZmdWRtYUVrYyIsIm9yaWdpbiI6Imh0dHBzOi8vYXVnbWVudGVkLWNsYXNzcm9vbS1rYWJmLnZlcmNlbC5hcHAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
#                                                                                                                                          "transports": ["internal"], "publicKeyAlgorithm": -257, "publicKey": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx3ybpCNdvjpJz2-8YrFTNoMyCwtXpDC7p-3GQTCoh9Ex1Ver9vspEe6_cH9pXWVtwi_6bOMnFUgYhlng86VFT_DibLJJU7DjHXKnr6wp2rIq0mEDfh98Kd8oU1Quh4N1rIILDzW3kZ1gwtZWKOzmbjX8-IORsge7mIcelpfakIbHB1yOgDpMlx02LX2MqC39ZDMyYFyhEGXFGkeEGVrU_Wmx6sxSP3XGtao2A1ttjI4vZ19y443ghfwuNZFGDqVg1wUmN2X9xlnaSJdPrXiazq2puslm9ymmJ6ktCua6j5Vd3WvBGn6SMF3rKXtkQ-Cu8zWwt2vqs-J1JS_314LLmQIDAQAB", "authenticatorData": "UqQfTrZcyyiUtScGG6dIfyg1it78fY-Ey_XPk07MeplFAAAAAGAosBex1EwCtLOvza_Ja7IAICfC3BVbyOCKEtpYXNdYyl0vB3mC8zm2U7R-m0AufPVHpAEDAzkBACBZAQDHfJukI12-OknPb7xisVM2gzILC1ekMLun7cZBMKiH0THVV6v2-ykR7r9wf2ldZW3CL_ps4ycVSBiGWeDzpUVP8OJssklTsOMdcqevrCnasirSYQN-H3wp3yhTVC6Hg3WsggsPNbeRnWDC1lYo7OZuNfz4g5GyB7uYhx6Wl9qQhscHXI6AOkyXHTYtfYyoLf1kMzJgXKEQZcUaR4QZWtT9abHqzFI_dca1qjYDW22Mji9nX3LjjeCF_C41kUYOpWDXBSY3Zf3GWdpIl0-teJrOram6yWb3KaYnqS0K5rqPlV3da8EafpIwXespe2RD4K7zNbC3a-qz4nUlL_fXgsuZIUMBAAE"}, "type": "public-key", "clientExtensionResults": {}, "authenticatorAttachment": "platform"}

#     response = client.post(
#         url="/verify-registration-response",
#         headers={"Authorization": "Bearer " + test_access_token},
#         json=request
#     )
#     assert response.status_code == 200
#     assert response.json() == {"verified": True}


# def test_generate_authentication_options(session: Session, client: TestClient):
#     student = Student(
#         matric_number="21CG029882", password=get_password_hash("password"))

#     session.add(student)
#     session.commit()

#     response = client.get(
#         url="/generate-authentication-options",
#         headers={"Authorization": "Bearer " + test_access_token}
#     )

#     assert response.status_code == 200


# def test_verify_authentication_options(session: Session, client: TestClient):
#     student = Student(
#         matric_number="21CG029882", password=get_password_hash("password"))

#     session.add(student)
#     session.commit()

#     response = client.post(
#         url="/verify-authentication-response",
#         headers={"Authorization": "Bearer " + test_access_token}
#     )
#     assert response.status_code == 200
#     assert response.json() == {"verified": True}


def test_refresh(session: Session, client: TestClient):
    student = Student(
        matric_number="21CG029882", password=get_password_hash("password"))

    session.add(student)
    session.commit()
    response = client.post(
        "/refresh",
        json={"refresh_token": test_refresh_token},
        headers={"Authorization": "Bearer " + test_access_token}
    )

    assert response.status_code == 200
    assert "new_access_token" in response.json() and "token_type" in response.json()


def test_refresh_incorrect_access_token(session: Session, client: TestClient):
    student = Student(
        matric_number="21CG029882", password=get_password_hash("password"))

    session.add(student)
    session.commit()
    response = client.post(
        "/refresh",
        json={"refresh_token": test_refresh_token},
        headers={"Authorization": "Bearer k" + test_access_token}
    )

    assert response.status_code == 401


def test_refresh_incorrect_refresh_token(session: Session, client: TestClient):
    student = Student(
        matric_number="21CG029882", password=get_password_hash("password"))

    session.add(student)
    session.commit()
    response = client.post(
        "/refresh",
        json={"refresh_token": test_refresh_token + "d"},
        headers={"Authorization": "Bearer " + test_access_token}
    )

    assert response.status_code == 401

# So i am not going to be testing those webauthn endpoints because i need the front end for it to work really well
