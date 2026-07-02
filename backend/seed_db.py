import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, Base, AsyncSessionLocal
from app.models import (
    User, Project, Milestone, Todo, TimelineEvent,
    Payment, Contract, PendingThing, Reminder,
    ConversationLog, EntityMemory, SessionSummary, SessionState
)
from app.utils.auth_helper import get_password_hash

async def seed_data():
    print("Connecting to database and dropping existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Recreating database tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Tables recreated. Seeding fake data...")
    async with AsyncSessionLocal() as session:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email = os.getenv("SMTP_USER") or "vivek727sumo@gmail.com"
        
        # 1. Create Default User
        user = User(
            id=uuid.uuid4(),
            name="Default Workspace User",
            email=email,
            password_hash=get_password_hash("password")
        )
        session.add(user)
        await session.flush()
        user_id = user.id
        print(f"Created user {email} with ID: {user_id}")

        # Define project models
        now = datetime.now(timezone.utc)
        
        # 2. Projects
        p1 = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            title="Project Alpha CRM",
            description="Custom enterprise broker portal with dynamic map integration, lead matching, automated notification follow-ups, and organization dashboard.",
            status="developing",
            priority="critical",
            deadline=now + timedelta(days=21),
            total_amount=Decimal("150000.00"),
            summary="A comprehensive CRM and search portal for property brokers to manage inventory, follow up on leads, and broadcast listings to client lists automatically.",
            notepad="Client wants weekly updates on Friday.\nPreferred communication channel: Email/Slack.\nEnsure payment milestones are synchronized with sprint releases.\nNeed Mapbox token from client.",
            risks=["API rate limits with Mapbox", "Delayed client feedback on custom CRM flow"]
        )

        p2 = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            title="Project Beta Mobile SDK",
            description="React Native/Expo app for social shopping and gamified product reviews, featuring Google Play Billing integration.",
            status="developing",
            priority="high",
            deadline=now + timedelta(days=35),
            total_amount=Decimal("250000.00"),
            summary="A native social commerce application integrating gamified product reviews, direct checkout, and Google Play subscription products.",
            notepad="AAB build keys configured. In-app purchases testing active. Deployment target: mid-July. Play Store console access is verified.",
            risks=["App Store review policy delays for gamified reviews", "Expo SDK upgrade compatibility"]
        )

        p3 = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            title="Project Gamma Fleet Dashboard",
            description="Next.js dashboard for driver payroll, roster scheduling, and route optimization metrics.",
            status="planning",
            priority="medium",
            deadline=now + timedelta(days=60),
            total_amount=Decimal("180000.00"),
            summary="Interactive dispatch system and driver workspace featuring real-time map plotting, automated payroll invoicing, and shift management.",
            notepad="First wireframe demo scheduled for Monday. Draft API schemas for driver check-ins.",
            risks=["Integration of real-time GPS tracking latency", "Multiple time-zone support for payroll"]
        )

        p4 = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            title="Project Delta Identity Guidelines",
            description="Complete brand guidelines, design system, typography, vector assets, and marketing collateral.",
            status="finished",
            priority="low",
            deadline=now - timedelta(days=10),
            total_amount=Decimal("50000.00"),
            summary="Branding project updating enterprise corporate identity, color system, fonts, presentation decks, and web design style guide.",
            notepad="All deliverables signed off. Final payment received.",
            risks=[]
        )

        session.add_all([p1, p2, p3, p4])
        await session.flush()

        # 3. Milestones
        # Project Alpha Milestones
        m1_1 = Milestone(
            id=uuid.uuid4(), project_id=p1.id, title="Wireframes & Architecture",
            description="UI/UX wireframes approval and database schema finalization.",
            start_date=now - timedelta(days=15), end_date=now - timedelta(days=5), status="achieved"
        )
        m1_2 = Milestone(
            id=uuid.uuid4(), project_id=p1.id, title="Core Map Integration",
            description="Listing map search with clustering and filters.",
            start_date=now - timedelta(days=4), end_date=now + timedelta(days=5), status="active"
        )
        m1_3 = Milestone(
            id=uuid.uuid4(), project_id=p1.id, title="CRM & Notification Engine",
            description="Notification triggers and lead tracking logs.",
            start_date=now + timedelta(days=6), end_date=now + timedelta(days=18), status="planned"
        )

        # Project Beta Milestones
        m2_1 = Milestone(
            id=uuid.uuid4(), project_id=p2.id, title="Authentication & Profile",
            description="OAuth onboarding and secure keychain token storage.",
            start_date=now - timedelta(days=20), end_date=now - timedelta(days=10), status="achieved"
        )
        m2_2 = Milestone(
            id=uuid.uuid4(), project_id=p2.id, title="Google Play Billing",
            description="In-app product purchases and subscription handling.",
            start_date=now - timedelta(days=5), end_date=now + timedelta(days=7), status="active"
        )
        m2_3 = Milestone(
            id=uuid.uuid4(), project_id=p2.id, title="Social Review Feed",
            description="Video upload stream and interactive reaction cards.",
            start_date=now + timedelta(days=8), end_date=now + timedelta(days=28), status="planned"
        )

        # Project Gamma Milestones
        m3_1 = Milestone(
            id=uuid.uuid4(), project_id=p3.id, title="API Specifications",
            description="Drafting payload contracts for driver check-ins and tracking endpoints.",
            start_date=now, end_date=now + timedelta(days=10), status="active"
        )

        session.add_all([m1_1, m1_2, m1_3, m2_1, m2_2, m2_3, m3_1])
        await session.flush()

        # 4. Todos (Sprint tasks)
        # Project Alpha Todos
        t1_1 = Todo(
            project_id=p1.id, milestone_id=m1_1.id, title="Define SQL database schemas",
            description="Write migrations for listings, agents, and lead assignments.",
            priority="high", status="done", estimated_hours=Decimal("12.0"), actual_hours=Decimal("14.5")
        )
        t1_2 = Todo(
            project_id=p1.id, milestone_id=m1_2.id, title="Implement Mapbox GL canvas component",
            description="Setup custom SVG markers for property pins.",
            priority="critical", status="in_progress", estimated_hours=Decimal("20.0"), due_date=now + timedelta(days=2)
        )
        t1_3 = Todo(
            project_id=p1.id, milestone_id=m1_2.id, title="Create listing details slide-over pane",
            description="Responsive overlay showing details of clicked marker.",
            priority="medium", status="todo", estimated_hours=Decimal("8.0"), due_date=now + timedelta(days=5)
        )
        t1_4 = Todo(
            project_id=p1.id, milestone_id=m1_3.id, title="Integrate Twilio API service",
            description="Create endpoints to broadcast updates on listing status.",
            priority="high", status="todo", estimated_hours=Decimal("15.0"), due_date=now + timedelta(days=12)
        )

        # Project Beta Todos
        t2_1 = Todo(
            project_id=p2.id, milestone_id=m2_1.id, title="Configure Firebase Apple Auth certificates",
            description="Setup secure credentials on iOS App Store Connect.",
            priority="high", status="done", estimated_hours=Decimal("6.0"), actual_hours=Decimal("5.5")
        )
        t2_2 = Todo(
            project_id=p2.id, milestone_id=m2_2.id, title="Debug duplicate Play Billing purchase token validation",
            description="Fix issue where some purchase tokens trigger duplicate registration callbacks.",
            priority="critical", status="in_progress", estimated_hours=Decimal("10.0"), due_date=now + timedelta(days=1)
        )
        t2_3 = Todo(
            project_id=p2.id, milestone_id=m2_2.id, title="Add restore subscriptions callback handler",
            description="Ensure user profiles are updated on license recovery.",
            priority="medium", status="review", estimated_hours=Decimal("5.0"), due_date=now + timedelta(days=3)
        )
        t2_4 = Todo(
            project_id=p2.id, milestone_id=m2_3.id, title="Implement video reviews compress script",
            description="Optimize mobile video uploads to reduce server bandwidth.",
            priority="low", status="todo", estimated_hours=Decimal("16.0"), due_date=now + timedelta(days=20)
        )

        # Project Gamma Todos
        t3_1 = Todo(
            project_id=p3.id, milestone_id=m3_1.id, title="Setup boilerplates with Tailwind and Next.js",
            description="Initialize layout grids, router setups, and baseline theme variables.",
            priority="medium", status="in_progress", estimated_hours=Decimal("12.0"), due_date=now + timedelta(days=4)
        )

        # Project Delta Todos
        t4_1 = Todo(
            project_id=p4.id, title="Publish corporate vector brand assets",
            description="Upload logo versions to shared storage folder.",
            priority="low", status="done", estimated_hours=Decimal("4.0"), actual_hours=Decimal("4.0")
        )

        session.add_all([t1_1, t1_2, t1_3, t1_4, t2_1, t2_2, t2_3, t2_4, t3_1, t4_1])
        await session.flush()

        # 5. Timeline Events
        # Project Alpha Events
        te1_1 = TimelineEvent(
            project_id=p1.id, event_name="Wireframes Sign-off", event_type="milestone",
            event_date=now - timedelta(days=5), status="completed", notes="Client approved wireframes via call."
        )
        te1_2 = TimelineEvent(
            project_id=p1.id, event_name="Advance Payment Received", event_type="payment",
            event_date=now - timedelta(days=4), status="completed", notes="Advance milestone of 30,000 INR."
        )
        te1_3 = TimelineEvent(
            project_id=p1.id, event_name="Map Clustering Deadline", event_type="task_deadline",
            event_date=now + timedelta(days=2), status="pending", notes="Must deploy map search demo."
        )

        # Project Beta Events
        te2_1 = TimelineEvent(
            project_id=p2.id, event_name="Play Console Setup", event_type="milestone",
            event_date=now - timedelta(days=12), status="completed", notes="Configured billing profiles."
        )
        te2_2 = TimelineEvent(
            project_id=p2.id, event_name="Play Billing Demo Release", event_type="milestone",
            event_date=now + timedelta(days=7), status="pending", notes="Sandbox testing cycle complete."
        )

        # Project Gamma Events
        te3_1 = TimelineEvent(
            project_id=p3.id, event_name="API Wireframe Synced", event_type="meeting",
            event_date=now + timedelta(days=3), status="pending", notes="Synchronize rosters API endpoints with team."
        )

        session.add_all([te1_1, te1_2, te1_3, te2_1, te2_2, te3_1])
        await session.flush()

        # 6. Payments
        # Project Alpha Payments
        pay1_1 = Payment(
            project_id=p1.id, amount=Decimal("30000.00"), payment_type="Advance",
            status="received", received_date=now - timedelta(days=4), notes="Advance deposit for wireframes."
        )
        pay1_2 = Payment(
            project_id=p1.id, amount=Decimal("60000.00"), payment_type="Partial",
            status="pending", due_date=now + timedelta(days=10), notes="Release milestone on CRM completion."
        )
        pay1_3 = Payment(
            project_id=p1.id, amount=Decimal("60000.00"), payment_type="Final",
            status="pending", due_date=now + timedelta(days=25), notes="Final sign-off deployment."
        )

        # Project Beta Payments
        pay2_1 = Payment(
            project_id=p2.id, amount=Decimal("50000.00"), payment_type="Advance",
            status="received", received_date=now - timedelta(days=15), notes="Initial onboarding retainer."
        )
        pay2_2 = Payment(
            project_id=p2.id, amount=Decimal("100000.00"), payment_type="Partial",
            status="received", received_date=now - timedelta(days=1), notes="Milestone release on Profile Sync completion."
        )
        pay2_3 = Payment(
            project_id=p2.id, amount=Decimal("100000.00"), payment_type="Final",
            status="overdue", due_date=now - timedelta(days=2), notes="Deploy build release client review."
        )

        # Project Gamma Payments
        pay3_1 = Payment(
            project_id=p3.id, amount=Decimal("30000.00"), payment_type="Advance",
            status="pending", due_date=now + timedelta(days=5), notes="Upfront kickoff payment."
        )

        # Project Delta Payments
        pay4_1 = Payment(
            project_id=p4.id, amount=Decimal("50000.00"), payment_type="Final",
            status="received", received_date=now - timedelta(days=10), notes="Full contract payment received."
        )

        session.add_all([pay1_1, pay1_2, pay1_3, pay2_1, pay2_2, pay2_3, pay3_1, pay4_1])
        await session.flush()

        # 7. Contracts
        c1 = Contract(
            project_id=p1.id, client_name="Alpha Group Ltd",
            received_date=now - timedelta(days=10), signed_date=now - timedelta(days=8),
            contract_url="http://localhost:8000/uploads/contracts/alpha_crm_agreement.pdf",
            notes="NDA + Deliverable Schedule signed."
        )
        c2 = Contract(
            project_id=p2.id, client_name="Beta Solutions Inc",
            received_date=now - timedelta(days=18), signed_date=now - timedelta(days=17),
            contract_url="http://localhost:8000/uploads/contracts/beta_sdk_agreement.pdf",
            notes="Includes intellectual property transfer clauses."
        )

        session.add_all([c1, c2])
        await session.flush()

        # 8. PendingThings (Pending Items / Credentials)
        pt1 = PendingThing(
            project_id=p1.id, title="Mapbox API Access Key",
            description="Client needs to send production token or invite us to their billing console.",
            is_completed=False
        )
        pt2 = PendingThing(
            project_id=p2.id, title="Google Play Merchant Profile",
            description="Need merchant account invite to verify live transaction endpoints.",
            is_completed=False
        )
        pt3 = PendingThing(
            project_id=p2.id, title="Logo vector SVG export",
            description="Final exports for App Icon configurations.",
            is_completed=True, filename="logo_vector.svg", file_url="http://localhost:8000/uploads/logo_vector.svg",
            file_size=24500, file_type="image/svg+xml"
        )
        pt4 = PendingThing(
            project_id=p3.id, title="Driver payroll schemas CSV",
            description="Draft layout representing active driver rates and tax declarations.",
            is_completed=False
        )

        session.add_all([pt1, pt2, pt3, pt4])
        await session.flush()

        # 9. Reminders
        r1 = Reminder(
            user_id=user_id, title="Map Clustering Review with Project Alpha",
            description="Live demo of the listing cluster search components.",
            remind_at=now + timedelta(hours=3), channel="sms", status="pending"
        )
        r2 = Reminder(
            user_id=user_id, title="Play Store Build Verification",
            description="Verify AAB purchase callbacks testing console logs.",
            remind_at=now + timedelta(days=1), channel="both", status="pending"
        )
        r3 = Reminder(
            user_id=user_id, title="Client Sync: Weekly Report Draft",
            description="Draft deliverables summary for Project Beta and broadcast via email/Slack.",
            remind_at=now + timedelta(days=2), channel="email", status="pending"
        )

        session.add_all([r1, r2, r3])
        await session.flush()

        # 10. Entity Memory
        em1 = EntityMemory(
            user_id=user_id, entity_type="client", entity_name="Alpha Group Ltd",
            fact="Prefers demo updates on Slack rather than detailed email status reports."
        )
        em2 = EntityMemory(
            user_id=user_id, entity_type="project", entity_name="Project Beta Mobile SDK",
            fact="Uses Google Play Billing V5 libraries requiring active testing credentials on Google Play console."
        )
        em3 = EntityMemory(
            user_id=user_id, entity_type="payment", entity_name="Project Gamma Fleet Dashboard",
            fact="Requires 20% advance milestone clearance before initiating wireframes design."
        )

        session.add_all([em1, em2, em3])
        await session.flush()

        # 11. Conversation Logs (Demo Chats)
        s1 = uuid.uuid4()
        s2 = uuid.uuid4()

        # Chat Session 1: Project Alpha Map Setup Chat
        chat1_title = ConversationLog(
            user_id=user_id, session_id=s1, role="system", intent="session_title", content="Project Alpha Map Setup"
        )
        chat1_m1 = ConversationLog(
            user_id=user_id, session_id=s1, role="user", content="How do I setup map clustering in Project Alpha?",
            intent="project_query", entities={"project": "Project Alpha CRM"}
        )
        chat1_m2 = ConversationLog(
            user_id=user_id, session_id=s1, role="assistant",
            content="I suggest using **Mapbox GL JS** with the native clustering option (`cluster: true`).\n\n### Implementation Outline:\n1. Initialize Mapbox map instance in your React hook.\n2. Add a GeoJSON source with `cluster: true` and specify `clusterMaxZoom` (e.g. `14`).\n3. Create cluster and non-cluster layers using custom colors matching the dark theme.\n\n`📥 [Download Map Clustering Guide PDF](http://localhost:8000/uploads/guides/alpha_mapbox_guide.pdf)`\n\nLet me know if you would like me to draft the React component code!",
            intent="project_reply", entities={"reasoningSteps": ["Checking map libraries", "Selecting Mapbox", "Structuring steps"]}
        )

        # Chat Session 2: Google Play Billing Review
        chat2_title = ConversationLog(
            user_id=user_id, session_id=s2, role="system", intent="session_title", content="Project Beta Play Store Setup"
        )
        chat2_m1 = ConversationLog(
            user_id=user_id, session_id=s2, role="user", content="What is the current issue with Project Beta Play Store Billing?",
            intent="project_query", entities={"project": "Project Beta Mobile SDK"}
        )
        chat2_m2 = ConversationLog(
            user_id=user_id, session_id=s2, role="assistant",
            content="The current pending item is: **Google Play Merchant Profile invite**.\n\nWe need sandbox testing authorization to verify: \n- Real-time purchase notifications subscription validation.\n- Auto-renew purchase token verification hooks.\n\nI recommend sending a reminder template to Project Beta to clear this access.\n\n`📥 [Download Billing Setup PDF](http://localhost:8000/uploads/guides/beta_billing_setup.pdf)`",
            intent="project_reply", entities={"reasoningSteps": ["Checking todo tasks", "Locating Merchant Profile pending block"]}
        )

        session.add_all([chat1_title, chat1_m1, chat1_m2, chat2_title, chat2_m1, chat2_m2])
        await session.flush()

        # 12. Session Summaries
        sum1 = SessionSummary(
            user_id=user_id, session_id=s1, summary="Discussed Mapbox clustering configuration and integration steps for listing markers.",
            key_entities=["Project Alpha", "Mapbox GL JS"], key_actions=["suggested clustering parameters", "provided download guide"],
            message_count=2
        )
        sum2 = SessionSummary(
            user_id=user_id, session_id=s2, summary="Identified dependency on Project Beta Play Store Merchant console sandbox testing invite.",
            key_entities=["Project Beta Mobile SDK", "Google Play Console"], key_actions=["identified missing access role", "linked guide"],
            message_count=2
        )

        session.add_all([sum1, sum2])
        
        await session.commit()
        print("Demo database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
